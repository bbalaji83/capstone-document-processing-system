from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from loguru import logger


class Settings(BaseSettings):
    # App settings
    app_name: str = Field(
        default="Capstone Document Processing System"
    )
    app_version: str = Field(default="1.0.0")
    app_description: str = Field(
        default="AI-powered document Q&A system using RAG and ReActAgent"
    )
    debug: bool = Field(default=True)

    # Groq API
    groq_api_key: str = Field(..., env="GROQ_API_KEY")

    # ChromaDB settings
    chroma_db_path: str = Field(default="./data/chroma_db")
    chroma_collection_name: str = Field(default="documents")

    # Upload settings
    upload_dir: str = Field(default="./data/uploads")
    max_file_size_mb: int = Field(default=10)
    allowed_extensions: str = Field(
        default="pdf,txt,csv,xlsx,json,yaml"
    )

    # LLM settings
    llm_model: str = Field(default="llama3-8b-8192")
    llm_temperature: float = Field(default=0.1)
    llm_max_tokens: int = Field(default=1024)

    # Embedding settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2")

    # Retrieval settings
    top_k_results: int = Field(default=5)
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=50)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_allowed_extensions(self) -> list:
        return [
            ext.strip()
            for ext in self.allowed_extensions.split(",")
        ]


@lru_cache()
def get_settings() -> Settings:
    logger.info("Loading application settings")
    return Settings()