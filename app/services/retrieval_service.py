import chromadb
from llama_index.core import VectorStoreIndex, Settings as LlamaSettings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


class RetrievalService:
    """
    Handles semantic search against ChromaDB.
    Converts user questions to vectors and finds
    the most relevant document chunks.
    """

    def __init__(self):
        logger.info("Initializing RetrievalService...")

        # Step 1 — Initialize embedding model
        # Must use same model as embedding_service
        self.embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model
        )
        logger.info(
            f"Embedding model loaded: {settings.embedding_model}"
        )

        # Step 2 — Connect to existing ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_db_path
        )

        # Step 3 — Get existing collection
        # Collection must already exist from embedding_service
        try:
            self.collection = self.chroma_client.get_collection(
                settings.chroma_collection_name
            )
            logger.info(
                f"Connected to collection: "
                f"{settings.chroma_collection_name} "
                f"({self.collection.count()} chunks)"
            )
        except Exception as e:
            logger.warning(
                f"Collection not found: {str(e)}. "
                f"Upload documents first."
            )
            self.collection = None

        # Step 4 — Configure LlamaIndex
        LlamaSettings.embed_model = self.embed_model
        LlamaSettings.llm = None

        logger.info("RetrievalService initialized successfully")

    # ─────────────────────────────────────────
    # PUBLIC METHOD — called by react_agent.py
    # ─────────────────────────────────────────

    def retrieve(
        self,
        question: str,
        top_k: int = None
    ) -> dict:
        """
        Main entry point.
        Takes a question, searches ChromaDB,
        returns the most relevant chunks.
        """
        if top_k is None:
            top_k = settings.top_k_results

        logger.info(
            f"Retrieving top {top_k} chunks for: '{question}'"
        )

        # Check if collection exists and has data
        if self.collection is None:
            return {
                "status": "error",
                "question": question,
                "message": (
                    "No documents found in knowledge base. "
                    "Please upload documents first."
                ),
                "results": []
            }

        chunk_count = self.collection.count()
        if chunk_count == 0:
            return {
                "status": "error",
                "question": question,
                "message": (
                    "Knowledge base is empty. "
                    "Please upload documents first."
                ),
                "results": []
            }

        try:
            # Step 1 — Set up vector store from existing collection
            vector_store = ChromaVectorStore(
                chroma_collection=self.collection
            )
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )

            # Step 2 — Load existing index from ChromaDB
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=self.embed_model
            )

            # Step 3 — Create retriever
            retriever = index.as_retriever(
                similarity_top_k=min(top_k, chunk_count)
            )

            # Step 4 — Retrieve relevant nodes
            nodes = retriever.retrieve(question)

            # Step 5 — Format results
            results = []
            for rank, node in enumerate(nodes, start=1):
                results.append({
                    "rank": rank,
                    "text": node.get_content(),
                    "filename": node.metadata.get(
                        "filename", "unknown"
                    ),
                    "score": round(node.score, 4)
                    if node.score is not None else 0.0
                })

            logger.info(
                f"Retrieved {len(results)} chunks "
                f"for question: '{question}'"
            )

            return {
                "status": "success",
                "question": question,
                "chunks_found": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(
                f"Retrieval failed for '{question}': {str(e)}"
            )
            return {
                "status": "error",
                "question": question,
                "message": f"Retrieval failed: {str(e)}",
                "results": []
            }

    def get_context_text(self, question: str) -> str:
        """
        Convenience method.
        Returns retrieved chunks as a single formatted string
        ready to be injected into the LLM prompt.
        """
        result = self.retrieve(question)

        if result.get("status") != "success":
            logger.warning(
                f"Retrieval failed for context: "
                f"{result.get('message')}"
            )
            return ""

        results = result.get("results", [])
        if not results:
            logger.warning("No results returned from retrieval")
            return ""

        context_parts = []
        for item in results:
            context_parts.append(
                f"--- Source: {item.get('filename', 'unknown')} ---\n"
                f"{item.get('text', '')}"
            )

        context = "\n\n".join(context_parts)
        logger.info(
            f"Context built: {len(context)} characters "
            f"from {len(results)} chunks"
        )
        return context