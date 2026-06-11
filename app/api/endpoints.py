from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from loguru import logger
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.agents.react_agent import DocumentAgent
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

# Initialize services
document_service = DocumentService()
embedding_service = EmbeddingService()
agent = DocumentAgent()


# ─────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str
    top_k: int = 5


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────

@router.get("/health-check")
async def health_check():
    """Check if the API is running."""
    logger.info("Health check requested")
    stats = embedding_service.get_collection_stats()
    return {
        "status": "healthy",
        "message": "Capstone Document Processing System is running",
        "version": settings.app_version,
        "chromadb_chunks": stats.get("total_chunks", 0)
    }


# ─────────────────────────────────────────
# UPLOAD DOCUMENT
# ─────────────────────────────────────────

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(
        ...,
        description="Upload a PDF, TXT, CSV, Excel, JSON or YAML file"
    )
):
    """
    Upload and process a document.
    Validates file, extracts text, generates embeddings,
    and stores in ChromaDB for semantic search.
    Supported formats: PDF, TXT, CSV, XLSX, JSON, YAML
    """
    logger.info(f"Upload request received: {file.filename}")

    # Step 1 — Validate and extract text
    result = await document_service.validate_and_extract(file)

    if not result.get("valid"):
        logger.warning(
            f"Upload failed for {file.filename}: "
            f"{result.get('message')}"
        )
        raise HTTPException(
            status_code=400,
            detail=result.get("message")
        )

    # Step 2 — Save file to uploads directory
    file_contents = result.get("content", "").encode("utf-8")
    document_service.save_uploaded_file(
        file_contents, file.filename
    )

    # Step 3 — Generate embeddings and store in ChromaDB
    embed_result = embedding_service.embed_document(
        text=result.get("content"),
        filename=file.filename
    )

    if embed_result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=embed_result.get("message")
        )

    logger.info(
        f"Document fully processed: {file.filename}"
    )

    return {
        "status": "success",
        "filename": result.get("filename"),
        "file_type": result.get("file_type"),
        "size_kb": result.get("size_kb"),
        "char_count": result.get("char_count"),
        "chunk_count": embed_result.get("chunk_count"),
        "message": (
            f"Document processed and "
            f"{embed_result.get('chunk_count')} "
            f"chunks stored in ChromaDB."
        ),
        "next_step": "Ready for Q&A"
    }


# ─────────────────────────────────────────
# ASK QUESTION
# ─────────────────────────────────────────

@router.post("/ask-question")
async def ask_question(request: QuestionRequest):
    """
    Ask a natural language question about uploaded documents.
    Uses ReActAgent with RAG pipeline to generate
    grounded answers from your uploaded documents.
    """
    logger.info(
        f"Question received: '{request.question}'"
    )

    # Validate question not empty
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # Run the ReActAgent
    result = agent.ask(request.question)

    if result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=result.get("message")
        )

    logger.info(
        f"Answer generated for: '{request.question}'"
    )

    return {
        "status": "success",
        "question": result.get("question"),
        "answer": result.get("answer"),
        "message": result.get("message")
    }