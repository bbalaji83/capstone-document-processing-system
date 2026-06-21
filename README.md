# Capstone Document Processing System

AI-powered document Q&A system built with FastAPI, LlamaIndex, ChromaDB, and Groq. Upload documents in multiple formats and ask natural language questions — answers are grounded strictly in the uploaded content using Retrieval-Augmented Generation (RAG) and a single ReActAgent.

> Generative AI and ML Capstone Project — Illinois Tech / Edureka

---

## Overview

Users upload documents (PDF, TXT, CSV, Excel, JSON, YAML) through a REST API. The system extracts and chunks the text, generates vector embeddings, and stores them in ChromaDB. When a user asks a question, a single ReActAgent searches the knowledge base, retrieves relevant chunks, and uses Groq's Llama 3 model to generate a grounded, accurate answer — never relying on the LLM's general training knowledge.

Full architectural detail is in [`docs/Capstone_Architecture_Document.docx`](docs/Capstone_Architecture_Document.docx).

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI (with auto-generated Swagger UI) |
| Optional UI | Streamlit |
| AI orchestration | LlamaIndex |
| Agent | LlamaIndex ReActAgent (single agent, four reasoning roles) |
| LLM | Groq — Llama 3.1 8B Instant |
| Vector database | ChromaDB |
| Embedding model | sentence-transformers (all-MiniLM-L6-v2) |
| Containerization | Docker |

See [`docs/tech-stack.md`](docs/tech-stack.md) for full version details and rationale.

---

## Architecture

```
FastAPI Swagger UI / Streamlit UI
            ↓
    API endpoints (main.py)
            ↓
  Document │ Embedding │ Retrieval
   Service │  Service  │  Service
            ↓
   ReActAgent (LlamaIndex)
   plan → retrieve → reason → respond
            ↓
   ChromaDB        Groq (Llama 3)
```

Full diagram and component breakdown: [`docs/Capstone_Architecture_Document.docx`](docs/Capstone_Architecture_Document.docx)

---

## Setup Instructions

### Prerequisites
- Python 3.12.3
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repository
```bash
git clone https://github.com/bbalaji83/capstone-document-processing-system.git
cd capstone-document-processing-system
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Open `.env` and add your Groq API key:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 5. Run the application
```bash
python main.py
```

### 6. Open the API
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/api/v1/health-check](http://localhost:8000/api/v1/health-check)

### 7. (Optional) Run the Streamlit UI
In a second terminal, with the venv active and the API already running:
```bash
streamlit run streamlit_app.py --server.port 8501
```
Open [http://localhost:8501](http://localhost:8501)

---

## Running with Docker

```bash
docker build -t capstone-dps .
docker run -p 8000:8000 --env-file .env capstone-dps
```

The Dockerfile is validated end-to-end (build, install, startup) — see [`docs/known-limitations.md`](docs/known-limitations.md) §6–8 for the full deployment story, including why this project is demonstrated locally rather than on a continuously hosted free-tier URL.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/upload-document` | Upload a document (PDF, TXT, CSV, XLSX, JSON, YAML) |
| `POST` | `/api/v1/ask-question` | Ask a natural language question about uploaded documents |
| `GET` | `/api/v1/health-check` | Service status and current knowledge-base size |

Try every endpoint interactively at `/docs`.

---

## Example Usage

**Upload:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload-document" \
  -F "file=@travel_policy.txt"
```

**Ask a question:**
```bash
curl -X POST "http://localhost:8000/api/v1/ask-question" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the hotel limit for international travel?", "top_k": 3}'
```

---

## Project Structure
capstone-document-processing-system/
    app/
        api/          REST endpoint definitions
        services/     document, embedding, retrieval services
        agents/       ReActAgent definition
        core/         configuration management
        utils/        helper functions
    data/
        uploads/      saved uploaded documents
        chroma_db/    persistent vector database
    docs/             architecture, risk, and limitations documentation
    main.py           application entry point
    streamlit_app.py  optional visual interface
    requirements.txt  Python dependencies
    Dockerfile        container definition
    .env.example      environment variable template

## Documentation
- docs/Capstone_Architecture_Document.docx - Full system architecture, component deep dive, data flow
- docs/Capstone_Risk_Document.docx - Current-state and forward-looking production risk register
- docs/Capstone_Known_Limitations.docx- 8 evidenced findings from development and testing, with root-cause analysis
- docs/tech-stack.md - Technology choices and rationale
- docs/known-limitations.md - Source markdown for the limitations document above

## Key Design Decisions

**Single ReActAgent, not multi-agent: per course guidance, one agent performs four internal reasoning roles (plan, retrieve, reason, respond) rather than separate coordinating agents.
**FastAPI Swagger UI as primary interface: chosen over a custom UI because it is auto-generated at zero extra development cost while remaining fully interactive for reviewers. Streamlit was added afterward as an optional bonus layer on top of the same API.
**Local embedding model over an API: keeps the system fully free to run, at the cost of higher memory requirements during deployment (documented in limitations).
**Free-tier LLM (Llama 3.1 8B Instant): keeps the system free to build and run; documented tradeoffs in reliability are addressed through prompt design, temperature tuning, and max_iterations configuration rather than a paid model upgrade.

## Known Limitations
Extensively tested and documented — see docs/Capstone_Known_Limitations.docx for full details with log evidence. Summary:

Small/fast LLM occasionally skips the search tool before answering
Non-determinism on tabular comparison questions (fixed via temperature tuning)
Stale ChromaDB reference after external collection clear (fixed)
Conversation history caused inconsistent tool use across sequential questions (fixed)
Occasional ReAct output parse errors (self-healing via automatic retry)
Local Docker build constrained by Codespaces disk quota (resolved via cloud build)
Python patch version incompatibility on Render (fixed by pinning exact version)
Free-tier hosting RAM insufficient for embedding model (documented, accepted for capstone scope)

## Author
Balaji Baskaran — Generative AI and ML Capstone Project, June 2026