from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger
from app.services.document_service import DocumentService
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

# Initialize services
document_service = DocumentService()


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────

@router.get("/health-check")
async def health_check():
    """Check if the API is running."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "message": "Capstone Document Processing System is running",
        "version": settings.app_version
    }


# ─────────────────────────────────────────
# UPLOAD DOCUMENT
# ─────────────────────────────────────────

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(
        ..., description="Upload a PDF, TXT, CSV, Excel, JSON or YAML file"
    )
):
    """
    Upload and process a document.
    Validates the file type and size, extracts text,
    and prepares it for embedding.
    Supported formats: PDF, TXT, CSV, XLSX, JSON, YAML
    """
    logger.info(f"Upload request received: {file.filename}")

    # Validate and extract text from the document
    result = await document_service.validate_and_extract(file)

    # If validation or extraction failed, return error
    if not result.get("valid"):
        logger.warning(
            f"Upload failed for {file.filename}: "
            f"{result.get('message')}"
        )
        raise HTTPException(
            status_code=400,
            detail=result.get("message")
        )

    # Save file to uploads directory
    file_contents = result.get("content", "").encode("utf-8")
    document_service.save_uploaded_file(
        file_contents, file.filename
    )

    logger.info(
        f"Document processed successfully: {file.filename}"
    )

    return {
        "status": "success",
        "filename": result.get("filename"),
        "file_type": result.get("file_type"),
        "size_kb": result.get("size_kb"),
        "char_count": result.get("char_count"),
        "message": result.get("message"),
        "next_step": "Document ready for embedding"
    }


# ─────────────────────────────────────────
# ASK QUESTION
# ─────────────────────────────────────────

@router.post("/ask-question")
async def ask_question():
    """
    Ask a natural language question about uploaded documents.
    Full RAG pipeline implementation coming in Week 3.
    """
    return {
        "status": "endpoint ready",
        "message": "Q&A functionality coming in Week 3"
    }