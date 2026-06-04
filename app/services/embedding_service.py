import chromadb
from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings as LlamaSettings
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


class EmbeddingService:
    """
    Handles text chunking, embedding generation,
    and storage in ChromaDB.
    Uses LlamaIndex to orchestrate the pipeline.
    """

    def __init__(self):
        logger.info("Initializing EmbeddingService...")

        # Step 1 — Initialize embedding model
        self.embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model
        )
        logger.info(
            f"Embedding model loaded: {settings.embedding_model}"
        )

        # Step 2 — Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_db_path
        )
        logger.info(
            f"ChromaDB initialized at: {settings.chroma_db_path}"
        )

        # Step 3 — Get or create collection
        self.collection = (
            self.chroma_client.get_or_create_collection(
                settings.chroma_collection_name
            )
        )
        logger.info(
            f"Collection ready: {settings.chroma_collection_name}"
        )

        # Step 4 — Configure LlamaIndex global settings
        LlamaSettings.embed_model = self.embed_model
        LlamaSettings.llm = None

        # Step 5 — Initialize text splitter
        self.text_splitter = SentenceSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        logger.info(
            f"Text splitter configured: "
            f"chunk_size={settings.chunk_size}, "
            f"overlap={settings.chunk_overlap}"
        )

        logger.info("EmbeddingService initialized successfully")

    # ─────────────────────────────────────────
    # PUBLIC METHOD — called by endpoints.py
    # ─────────────────────────────────────────

    def embed_document(
        self,
        text: str,
        filename: str
    ) -> dict:
        """
        Main entry point.
        Takes extracted text, chunks it, generates embeddings,
        and stores everything in ChromaDB.
        Returns a summary of what was stored.
        """
        logger.info(
            f"Starting embedding for: {filename}"
        )

        try:
            # Step 1 — Create LlamaIndex Document object
            document = Document(
                text=text,
                metadata={
                    "filename": filename,
                    "source": filename
                }
            )

            # Step 2 — Split into chunks
            nodes = self.text_splitter.get_nodes_from_documents(
                [document]
            )
            chunk_count = len(nodes)
            logger.info(
                f"Text split into {chunk_count} chunks "
                f"for {filename}"
            )

            # Step 3 — Set up ChromaDB vector store
            vector_store = ChromaVectorStore(
                chroma_collection=self.collection
            )
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )

            # Step 4 — Build index
            # This generates embeddings and stores in ChromaDB
            index = VectorStoreIndex(
                nodes,
                storage_context=storage_context,
                embed_model=self.embed_model
            )

            logger.info(
                f"Successfully embedded and stored "
                f"{chunk_count} chunks for {filename}"
            )

            return {
                "status": "success",
                "filename": filename,
                "chunk_count": chunk_count,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "embedding_model": settings.embedding_model,
                "collection": settings.chroma_collection_name,
                "message": (
                    f"Successfully created {chunk_count} "
                    f"embeddings and stored in ChromaDB."
                )
            }

        except Exception as e:
            logger.error(
                f"Embedding failed for {filename}: {str(e)}"
            )
            return {
                "status": "error",
                "filename": filename,
                "message": f"Embedding failed: {str(e)}"
            }

    # ─────────────────────────────────────────
    # UTILITY METHODS
    # ─────────────────────────────────────────

    def get_collection_stats(self) -> dict:
        """Returns stats about what's stored in ChromaDB."""
        count = self.collection.count()
        logger.info(f"Collection count: {count}")
        return {
            "collection_name": settings.chroma_collection_name,
            "total_chunks": count,
            "embedding_model": settings.embedding_model
        }

    def clear_collection(self) -> dict:
        """Clears all documents from ChromaDB collection."""
        self.chroma_client.delete_collection(
            settings.chroma_collection_name
        )
        self.collection = (
            self.chroma_client.get_or_create_collection(
                settings.chroma_collection_name
            )
        )
        logger.info("ChromaDB collection cleared")
        return {
            "status": "success",
            "message": "Collection cleared successfully"
        }