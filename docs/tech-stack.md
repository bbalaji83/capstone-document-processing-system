# Capstone Document Processing System
## Tech Stack Document

---

### Project Overview
An AI-powered document Q&A system that allows users to upload enterprise 
documents and ask natural language questions. The system uses Retrieval-Augmented 
Generation (RAG) and a ReActAgent to retrieve relevant content and generate 
grounded responses.

---

### Tech Stack

#### 1. Development Environment
| Component        | Choice                  | Reason                                      |
|------------------|-------------------------|---------------------------------------------|
| Environment      | GitHub Codespaces       | Zero setup, browser-based, Linux-based      |
| Language         | Python 3.12.1           | Industry standard for AI/ML projects        |
| Version Control  | GitHub                  | Free, cloud-based, required for submission  |

---

#### 2. UI Layer
| Component        | Choice                  | Reason                                      |
|------------------|-------------------------|---------------------------------------------|
| UI Framework     | Streamlit               | Simplest AI app UI, free cloud hosting      |
| Hosting          | Streamlit Community Cloud | Free, connects directly to GitHub repo    |

---

#### 3. API Layer
| Component        | Choice                  | Reason                                      |
|------------------|-------------------------|---------------------------------------------|
| API Framework    | FastAPI                 | Recommended by instructor, auto Swagger docs|
| ASGI Server      | Uvicorn                 | Required to run FastAPI                     |
| Hosting          | Render                  | Free tier, public URL for reviewers         |

---

#### 4. AI Framework
| Component        | Choice                  | Reason                                      |
|------------------|-------------------------|---------------------------------------------|
| AI Framework     | LlamaIndex              | Specified by instructor                     |
| Agent Type       | ReActAgent              | Single agent — plan, retrieve, reason, respond |
| Embedding Model  | sentence-transformers   | Free, runs locally, no API cost             |

---

#### 5. LLM
| Component        | Choice                  | Reason                                      |
|------------------|-------------------------|---------------------------------------------|
| LLM Provider     | Groq                    | Free tier, fast inference, no credit card   |
| Model            | Llama 3 (via Groq)      | Open source, high quality, free             |

---

#### 6. Vector Database
| Component        | Choice                  | Reason                                      |
|------------------|-------------------------|---------------------------------------------|
| Vector Store     | ChromaDB                | Developer friendly, runs locally, no setup  |
| Storage          | Local disk (in-process) | No external service needed                  |

---

#### 7. Document Ingestion
| Format  | Library        |
|---------|----------------|
| PDF     | pypdf          |
| TXT     | os (built-in)  |
| CSV     | pandas         |
| Excel   | pandas + openpyxl |
| JSON    | json (built-in)|
| YAML    | pyyaml         |

---

#### 8. Reliability and Safety
| Component        | Choice                  | Reason                                      |
|------------------|-------------------------|---------------------------------------------|
| Input Validation | Pydantic                | Built into FastAPI, automatic validation    |
| Retry Logic      | Tenacity                | Handles Groq API rate limit retries         |
| Logging          | Loguru                  | Clean, simple logging                       |
| Env Variables    | python-dotenv           | Keeps API keys out of source code           |

---

#### 9. Deployment
| Component        | Choice                  | Reason                                      |
|------------------|-------------------------|---------------------------------------------|
| Containerization | Docker                  | Required by instructor for deployment       |
| Backend Hosting  | Render                  | Free, Docker-based deployment               |
| Frontend Hosting | Streamlit Community Cloud | Free, GitHub-connected                    |

---

### Architecture Summary