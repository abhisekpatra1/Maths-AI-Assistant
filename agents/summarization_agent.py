"""
Summarization Agent (Gemini Version)
Creates concise summaries of medical documents using Google Gemini
"""

from typing import List
from loguru import logger
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from services.vector_store import VectorStoreService


class SummarizationAgent:
    """
    Specialized agent for generating summaries of medical content (Gemini-based)
    """

    def __init__(self):
        # Useing "gemini-2.5-flash" for faster/cheaper inference
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
        logger.info("Summarization Agent (Gemini) initialized")

    async def generate_summary(self, session_id: str, vector_store: VectorStoreService) -> str:
        """
        Generate comprehensive summary of all documents
        """
        try:
            query = "medical findings clinical summary patient information"
            documents = vector_store.similarity_search(session_id, query, k=10)

            if not documents:
                return "No documents available for summarization."

            combined_content = self._prepare_content(documents)
            summary = self._create_summary(combined_content)

            logger.info("Summary generated successfully")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise

    async def summarize_section(self, content: str) -> str:
        """Summarize specific section content"""
        try:
            summary = self._create_summary(content)
            return summary
        except Exception as e:
            logger.error(f"Error summarizing section: {str(e)}")
            raise

    def _prepare_content(self, documents: List[Document]) -> str:
        """Prepare document content for summarization"""
        content_parts = []

        for doc in documents:
            content = doc.page_content
            source = doc.metadata.get("source", "Unknown")
            content_parts.append(f"[From {source}]\n{content}\n")

        return "\n".join(content_parts)

    def _create_summary(self, content: str) -> str:
        """Generate summary using Gemini"""

        prompt = ChatPromptTemplate.from_template(
            """You are a medical document summarization expert. 
            Create a comprehensive yet concise summary of the following medical content.

            Guidelines:
            - Highlight key medical findings and observations
            - Include important patient information if present
            - Mention significant clinical data, test results, or diagnoses
            - Use clear, professional medical language
            - Structure the summary logically
            - Keep the summary between 200–400 words
            - Do not bold any of the word or sentence

            Content to summarize:
            {content}

            Summary:"""
        )

        # Truncate overly long inputs
        max_content_length = 10000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n...[content truncated]"

        messages = prompt.format_messages(content=content)
        response = self.llm.invoke(messages)

        return response.content
