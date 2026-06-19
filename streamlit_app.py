import streamlit as st
import requests

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Capstone Document Processing System",
    page_icon="📄",
    layout="centered"
)

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────

st.title("📄 Capstone Document Processing System")
st.caption(
    "AI-powered document Q&A using RAG and ReActAgent"
)

# Check API health
try:
    health = requests.get(
        f"{API_BASE_URL}/health-check", timeout=5
    )
    if health.status_code == 200:
        data = health.json()
        st.success(
            f"✅ API is running — "
            f"{data.get('chromadb_chunks', 0)} chunks "
            f"in knowledge base"
        )
    else:
        st.error("⚠️ API is not responding correctly")
except requests.exceptions.ConnectionError:
    st.error(
        "❌ Cannot connect to API. "
        "Make sure main.py is running on port 8000."
    )
    st.stop()

st.divider()

# ─────────────────────────────────────────
# UPLOAD SECTION
# ─────────────────────────────────────────

st.header("1. Upload Document")
st.caption("Supported formats: PDF, TXT, CSV, Excel, JSON, YAML")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["pdf", "txt", "csv", "xlsx", "json", "yaml"]
)

if uploaded_file is not None:
    if st.button("Upload and Process", type="primary"):
        with st.spinner("Processing document..."):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }
            try:
                response = requests.post(
                    f"{API_BASE_URL}/upload-document",
                    files=files,
                    timeout=60
                )
                if response.status_code == 200:
                    result = response.json()
                    st.success(
                        f"✅ {result.get('message')}"
                    )
                    st.json({
                        "filename": result.get("filename"),
                        "chunks_created": result.get(
                            "chunk_count"
                        ),
                        "characters_extracted": result.get(
                            "char_count"
                        )
                    })
                else:
                    error_detail = response.json().get(
                        "detail", "Unknown error"
                    )
                    st.error(f"❌ {error_detail}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {str(e)}")

st.divider()

# ─────────────────────────────────────────
# Q&A SECTION
# ─────────────────────────────────────────

st.header("2. Ask a Question")
st.caption(
    "Ask anything about your uploaded documents"
)

question = st.text_input(
    "Your question",
    placeholder="e.g. What is the refund policy?"
)

if st.button("Ask", type="primary"):
    if not question or not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/ask-question",
                    json={"question": question, "top_k": 5},
                    timeout=60
                )
                if response.status_code == 200:
                    result = response.json()
                    st.subheader("💬 Answer")
                    st.write(result.get("answer"))
                else:
                    error_detail = response.json().get(
                        "detail", "Unknown error"
                    )
                    st.error(f"❌ {error_detail}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {str(e)}")

st.divider()
st.caption(
    "Capstone Project — Generative AI and ML | "
    "Built with FastAPI, LlamaIndex, ChromaDB, and Groq"
)