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

*Document version: 1.1 — June 2026*