from fastapi import APIRouter
from loguru import logger

router = APIRouter()


@router.get("/health-check")
async def health_check():
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "message": "Capstone Document Processing System is running"
    }


@router.post("/upload-document")
async def upload_document():
    # Full implementation coming in Week 3
    return {
        "status": "endpoint ready",
        "message": "Upload functionality coming soon"
    }


@router.post("/ask-question")
async def ask_question():
    # Full implementation coming in Week 3
    return {
        "status": "endpoint ready",
        "message": "Q&A functionality coming soon"
    }