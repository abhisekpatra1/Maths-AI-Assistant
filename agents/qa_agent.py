"""
Q&A Agent (Gemini Version)
Retrieval-Augmented Generation for answering medical questions
"""

from typing import Dict, List
from loguru import logger
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from services.vector_store import VectorStoreService
from services.session_manager import SessionManager
from langchain_core.prompts import ChatPromptTemplate

class QAAgent:
    """
    Specialized agent for question answering using RAG (Gemini-based)
    Maintains conversation context and memory
    """

    def __init__(self, vector_store: VectorStoreService, session_manager: SessionManager):
        self.vector_store = vector_store
        self.session_manager = session_manager
        # Using Gemini 2.5 Flash — faster and cheaper, suitable for interactive RAG
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)
        logger.info("Q&A Agent (Gemini) initialized")

    async def answer_question(self, session_id: str, question: str) -> Dict:
        """
        Answer question using RAG with conversation history
        """
        try:
            # Retrieve relevant documents
            relevant_docs = self.vector_store.similarity_search(
                session_id, question, k=5
            )

            if not relevant_docs:
                return {
                    "answer": "I couldn't find relevant information in the uploaded documents to answer your question.",
                    "sources": [],
                }

            # Build context from retrieved documents
            context = self._build_context(relevant_docs)
            sources = self._extract_sources(relevant_docs)

            # Get conversation history
            history = self.session_manager.get_history(session_id)

            # Generate answer
            answer = self._generate_answer(question, context, history)

            logger.info(f"Generated answer for question: {question[:50]}...")

            return {
                "answer": answer,
                "sources": sources,
            }

        except Exception as e:
            logger.error(f"Error in Q&A: {str(e)}")
            raise

    def _build_context(self, documents: List) -> str:
        """Build context string from retrieved documents"""
        context_parts = []

        for i, doc in enumerate(documents, 1):
            content = doc.page_content
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "")

            page_info = f" (Page {page})" if page else ""
            context_parts.append(f"[Document {i} from {source}{page_info}]\n{content}\n")

        return "\n".join(context_parts)

    def _extract_sources(self, documents: List) -> List[str]:
        """Extract unique sources from documents"""
        sources = set()

        for doc in documents:
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "")

            if page:
                sources.add(f"{source} (Page {page})")
            else:
                sources.add(source)

        return list(sources)

    def _generate_answer(self, question: str, context: str, history: List[Dict]) -> str:
        """Generate answer using Gemini LLM with context and history"""

        # System role prompt
        messages = [
            SystemMessage(
                content="""You are a Mathematics document assistant. Answer questions based on the provided context from documents and files.

                Guidelines:
                1. Answer using information explicitly stated in the provided CHUNK context and Chat History.
                2. If the answer is found in Chat History (not in the CHUNKs), write:
                "In Chat History I got the information."
                Then provide the answer based on Chat History content.
                3. If the information is NOT found in the context or chat history, respond formally like this:
                "Apologies, but this specific information is not mentioned in the provided document or chat history. 
                However, the document discusses related details such as [summarize 2–3 relevant lines from the context and cite them properly]."
                4. Do NOT use any external knowledge or assumptions.
                5. Do NOT hallucinate. If something is not explicitly mentioned, clearly state that it is not available.
                6. Maintain a formal, concise, and citation-accurate tone throughout your response.
                7. Do not use citations.
                8. If an email is found → convert to:  <a href="mailto:EMAIL">EMAIL</a>
                9. If a phone number is found → convert to:  <a href="tel:PHONE">PHONE</a>
                """
                        )
        ]

        # Add conversation history (last 20 turns)
        for msg in history[-20:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        # Add the current query and context
        prompt = f"""Based on the following medical documents, please answer the question.

                Context from documents:
                {context}

                Question: {question}

                Answer:"""

        messages.append(HumanMessage(content=prompt))

        # Generate answer using Gemini
        response = self.llm.invoke(messages)
        return response.content
