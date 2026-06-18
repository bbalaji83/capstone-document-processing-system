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

*Document version: 1.0 — June 2026*