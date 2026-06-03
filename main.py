from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import os

from app.core.config import get_settings
from app.api.endpoints import router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────
    logger.info("Starting Capstone Document Processing System")
    logger.info(f"App version: {settings.app_version}")
    logger.info(f"LLM model: {settings.llm_model}")
    logger.info(f"Embedding model: {settings.embedding_model}")

    # Create required directories if they don't exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_db_path, exist_ok=True)
    logger.info(f"Upload directory ready: {settings.upload_dir}")
    logger.info(f"ChromaDB directory ready: {settings.chroma_db_path}")

    yield

    # ── Shutdown ─────────────────────────────────────
    logger.info("Shutting down Capstone Document Processing System")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    docs_url="/docs",        # Swagger UI at /docs
    redoc_url="/redoc",      # ReDoc UI at /redoc
    lifespan=lifespan
)

# CORS middleware — allows browser clients to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health-check"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )