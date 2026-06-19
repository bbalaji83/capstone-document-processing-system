from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.groq import Groq
from llama_index.core import Settings as LlamaSettings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from app.core.config import get_settings
from app.services.retrieval_service import RetrievalService

settings = get_settings()


class DocumentAgent:
    """
    ReActAgent that answers questions about uploaded documents.
    Uses retrieval tool to find relevant chunks from ChromaDB
    then uses Groq LLM to generate grounded answers.
    
    Agent Roles (all within single ReActAgent loop):
    - Planner   : decides what steps to take
    - Retriever : calls search tool to find relevant chunks
    - Reasoning : analyses retrieved context
    - Response  : generates final grounded answer
    """

    def __init__(self):
        logger.info("Initializing DocumentAgent...")

        # Step 1 — Initialize embedding model
        self.embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model
        )

        # Step 2 — Configure LlamaIndex global settings
        LlamaSettings.embed_model = self.embed_model

        # Step 3 — Initialize Groq LLM
        self.llm = Groq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        logger.info(f"LLM initialized: {settings.llm_model}")

        # Step 4 — Initialize retrieval service
        self.retrieval_service = RetrievalService()
        logger.info("Retrieval service connected to agent")

        # Step 5 — Create tools for the agent
        self.tools = self._create_tools()
        logger.info(f"Tools created: {len(self.tools)}")

        # Step 6 — Create ReActAgent
        self.agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            max_iterations=10,
            context=self._get_system_prompt()
        )
        logger.info("ReActAgent initialized successfully")

    # ─────────────────────────────────────────
    # PUBLIC METHOD — called by endpoints.py
    # ─────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8)
    )
    def ask(self, question: str) -> dict:
        """
        Main entry point.
        Takes a user question, runs the ReAct loop,
        returns a grounded answer.
        """
        logger.info(f"Agent received question: '{question}'")

        # Validate question
        if not question or len(question.strip()) == 0:
            return {
                "status": "error",
                "question": question,
                "answer": None,
                "message": "Question cannot be empty."
            }

        if len(question) > 1000:
            return {
                "status": "error",
                "question": question,
                "answer": None,
                "message": (
                    "Question too long. "
                    "Please keep it under 1000 characters."
                )
            }

        try:
            # Run the ReAct agent
            response = self.agent.chat(question)
            answer = str(response)

            logger.info(
                f"Agent generated answer: "
                f"{answer[:100]}..."
            )

            return {
                "status": "success",
                "question": question,
                "answer": answer,
                "message": "Answer generated successfully."
            }

        except Exception as e:
            logger.error(
                f"Agent failed for question "
                f"'{question}': {str(e)}"
            )
            return {
                "status": "error",
                "question": question,
                "answer": None,
                "message": f"Failed to generate answer: {str(e)}"
            }

    # ─────────────────────────────────────────
    # TOOL CREATION
    # ─────────────────────────────────────────

    def _create_tools(self) -> list:
        """
        Creates tools the ReActAgent can use.
        The agent reads the description to decide
        when and how to use each tool.
        """

        def search_documents(question: str) -> str:
            """
            Search uploaded documents for information
            relevant to the question.
            Returns the most relevant text chunks
            from the knowledge base.
            """
            logger.info(
                f"Tool called: search_documents('{question}')"
            )
            context = self.retrieval_service.get_context_text(
                question
            )
            if not context:
                return (
                    "No relevant information found in the "
                    "uploaded documents for this question."
                )
            return context

        search_tool = FunctionTool.from_defaults(
            fn=search_documents,
            name="search_documents",
            description=(
                "Use this tool to search through uploaded "
                "documents and find information relevant to "
                "the user's question. Input should be the "
                "question or key terms to search for. "
                "Always use this tool before answering "
                "any question about the documents."
            )
        )

        return [search_tool]

    # ─────────────────────────────────────────
    # SYSTEM PROMPT
    # ─────────────────────────────────────────

    def _get_system_prompt(self) -> str:
        """
        System prompt that instructs the agent
        how to behave.
        """
        return """You are a helpful AI assistant that answers 
questions based ONLY on the content of uploaded documents.

Your behavior rules:
1. ALWAYS use the search_documents tool first before answering
2. Base your answer ONLY on the retrieved document content
3. If the answer is not in the documents, say clearly:
   "I could not find information about this in the 
   uploaded documents."
4. Never make up information or use general knowledge
5. Always cite which document your answer comes from
6. Keep answers clear, concise, and accurate

You are grounded in the provided documents only."""