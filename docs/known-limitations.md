# Known Limitations and Challenges

## 1. Context Dilution in Mixed-Topic Knowledge Bases

**Observed behavior:**
When the ChromaDB knowledge base contains documents on very 
different topics (e.g. a short travel policy document alongside 
a large 12-chunk PDF on an unrelated subject), the ReActAgent 
occasionally fails to use a correctly retrieved chunk if it is 
surrounded by a larger volume of unrelated context.

**Root cause:**
The retrieval step (ChromaDB similarity search) correctly 
identifies the relevant chunk. However, when `top_k=5` chunks 
are combined into a single LLM prompt, a short relevant chunk 
can be "diluted" by several longer, unrelated chunks. This is a 
documented LLM behavior sometimes called "lost in the middle," 
and is more pronounced with smaller, faster models such as 
`llama-3.1-8b-instant` (chosen here for free-tier speed).

**Example:**
- Question: "What is the hotel limit for international travel?"
- Knowledge base: travel_policy.txt (1 chunk) + a 12-chunk PDF 
  on an unrelated topic
- Result: Agent retrieved the correct chunk (visible in logs) 
  but answered "I could not find information" because the 
  correct chunk was outweighed by surrounding unrelated content

**Why not fixed in this version:**
Mitigating this fully would require either a larger/more capable 
LLM, a re-ranking step after retrieval, or topic-aware chunk 
filtering — all of which add cost, complexity, or latency beyond 
the scope of this capstone's free-tier constraints.

**Confirmed through repeated testing:**
The same question ("Which employee has the highest salary?") 
was tested multiple times against an unchanged knowledge base. 
Results were inconsistent:
- Run 1: Correct answer (Raj Patel, Engineering, $92,000) — 
  54.88 seconds response time
- Run 2 (immediately after): Incorrect — "I could not find 
  information" — 1.39 seconds response time

Reviewing the full agent trace for Run 2 confirmed that 
retrieval correctly returned the chunk containing the answer 
as the FIRST of three retrieved chunks, immediately followed 
by a longer, denser, topically unrelated chunk from a PDF 
document. The LLM's final answer ignored the correct chunk 
entirely. This is strong evidence the failure is a genuine 
LLM attention limitation when relevant short content is 
immediately followed by longer unrelated content — not a 
retrieval bug, not a token limit issue, and not directly 
correlated with response time.

**Possible production improvements:**
- Add a re-ranking step (e.g. cross-encoder) after initial 
  retrieval to prioritize the most relevant chunk
- Reduce `top_k` when the knowledge base spans multiple unrelated 
  documents
- Use a larger LLM (e.g. `llama-3.3-70b-versatile`) for better 
  long-context reasoning
- Tag documents by topic/category and filter retrieval by topic 
  when known

**Follow-up experiment — does knowledge base size matter?**
To test whether the issue was caused specifically by the large 
12-chunk PDF, the experiment was repeated with a much smaller 
knowledge base: travel_policy.txt (1 chunk), employees.csv 
(1 chunk), and a short 4-page slide PDF (2 chunks) — 4 chunks 
total, compared to 14 in the original test.

The same question ("Which employee has the highest salary?") 
was run 3 times consecutively:
- Run 1: Correct (required additional ReAct iterations to 
  complete — see max_iterations note below)
- Run 2: Correct (completed cleanly)
- Run 3: Incorrect — agent skipped calling the search tool 
  entirely and answered "I could not find information" 
  without attempting retrieval

**Conclusion:** Knowledge base size and document length are 
not the primary cause. Even with a small, focused knowledge 
base, the LLM occasionally chose not to invoke the search tool 
at all before answering. This indicates the core limitation is 
inherent non-determinism in a small, fast LLM's decision of 
*whether* to use a tool — not the volume or dilution of 
retrieved context. Larger, more capable models are generally 
more reliable at consistent tool-use decisions; this tradeoff 
was accepted here in favor of free-tier speed and cost.

**Related fix — increased max_iterations:**
During this experiment, `max_iterations=5` was found to be too 
restrictive in some cases — the agent reached a correct answer 
in its reasoning but exceeded the iteration limit before 
formally returning it, producing a `None` result. Increasing 
`max_iterations` to `10` in `react_agent.py` resolved this 
specific failure mode.

---

## 2. LLM Non-Determinism on Tabular Data

**Observed behavior:**
When asking comparison questions over CSV data (e.g. "which 
employee has the highest salary"), the agent occasionally 
declined to answer even though the correct data was retrieved.

**Root cause:**
LLMs are not fully deterministic even at low temperature, and 
reasoning over raw delimited text (rather than a true table 
structure) requires the model to mentally parse and compare 
values, which is more error-prone than direct text retrieval.

**Fix applied:**
Lowered `LLM_TEMPERATURE` from `0.1` to `0.0` in `.env`, which 
significantly improved consistency in testing (multiple repeated 
queries returned correct, consistent answers after this change).

**Possible production improvements:**
- Pre-process structured data (CSV/Excel) into explicit 
  sentence-form facts before embedding, rather than raw 
  delimited text
- Use a dedicated structured-data query tool (e.g. pandas 
  query agent) for tabular files instead of pure semantic search

---

## 3. Stale ChromaDB Collection Reference After External Clear

**Observed behavior:**
Calling `clear_collection()` from a separate Python process while 
the FastAPI server is already running can leave the running 
server's `EmbeddingService` instance pointing to a stale, deleted 
ChromaDB collection reference, causing subsequent uploads to fail 
with an empty error message.

**Root cause:**
`EmbeddingService` and `RetrievalService` each hold their own 
`self.collection` reference, set once at initialization. Clearing 
the collection from outside the running server process does not 
update that in-memory reference.

**Fix:**
Restart the FastAPI server (`main.py`) after externally clearing 
ChromaDB, so services reinitialize against the current collection 
state.

**Production improvement:**
Add an admin endpoint to clear the collection through the running 
application itself (rather than a separate script), ensuring all 
service instances stay in sync.

---
---

## 4. Conversation History Causing Inconsistent Tool Use (Fixed)

**Observed behavior:**
When asking 3 questions in sequence using `agent.chat()`, the 
first 1-2 questions were answered correctly (with the search 
tool correctly invoked), but later questions in the same session 
sometimes skipped the search tool entirely and answered 
incorrectly with "I could not find information."

**Root cause:**
`agent.chat()` maintains conversation history across calls. As 
context accumulated from previous questions, the LLM sometimes 
assumed it already had enough information and skipped calling 
the search tool for new, unrelated questions.

**Fix applied:**
Changed `self.agent.chat(question)` to `self.agent.query(question)` 
in `react_agent.py`. `query()` treats each question as 
independent with no retained conversation history, which matches 
the intended use case — each API call to `/ask-question` should 
be a fresh, independent question about the documents, not part 
of an ongoing conversation. After this change, repeated testing 
showed consistently correct tool use across multiple sequential 
questions.

---

## 5. Occasional ReAct Output Format Parse Errors (Self-Healing)

**Observed behavior:**
After several tool calls in a single agent run, the LLM 
occasionally produced output that didn't match LlamaIndex's 
expected `Thought: / Action: / Answer:` format, triggering 
"Error: Could not parse output" and an automatic retry.

**Root cause:**
`llama-3.1-8b-instant` is a small, fast model. Smaller models 
are generally less reliable than larger ones at strictly 
following structured prompting formats like ReAct, especially 
after multiple reasoning steps.

**Outcome:**
LlamaIndex's built-in retry mechanism automatically reissued 
the request on parse failure. In testing, this self-corrected 
within 2-3 retries and ultimately produced the correct answer 
every time observed, at the cost of additional latency 
(up to ~90 seconds in one observed case).

**Possible production improvement:**
Use a larger, more format-reliable model (e.g. 
`llama-3.3-70b-versatile`) to reduce parse-retry frequency and 
latency, at the cost of slower/more expensive inference.

---

## Summary — Free-Tier Small-LLM Tradeoffs

All limitations documented above (sections 1, 4, and 5) trace 
back to the same underlying engineering tradeoff: this project 
uses `llama-3.1-8b-instant`, a small and fast model available 
on Groq's free tier, in order to keep the entire system free to 
build and run. This model is occasionally inconsistent in:
- Deciding whether to invoke the search tool (section 1)
- Maintaining reliable tool-use behavior across a conversation 
  (section 4, now fixed via `query()` instead of `chat()`)
- Strictly following the ReAct structured output format 
  (section 5, self-healing via automatic retry)

A production deployment with budget for a larger model (e.g. 
`llama-3.3-70b-versatile` or a paid-tier model) would likely 
see meaningfully improved consistency across all three areas, 
at increased cost and latency per request.

---

*Document version: 1.2 — June 2026*