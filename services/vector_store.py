"""
Vector Store Service
Manages document embeddings and similarity search using ChromaDB
Free version using HuggingFace embeddings (no API quota required)
"""

from typing import List
import os
from loguru import logger
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings


class VectorStoreService:
    """
    Service for managing vector database operations
    Handles document storage and retrieval using embeddings
    """

    def __init__(self, persist_directory: str = "data/chroma"):
        """
        Initialize vector store

        Args:
            persist_directory: Directory to persist ChromaDB data
        """

        # Load environment variables (optional)
        load_dotenv()

        # Create persistence directory
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        # Free, offline embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Cache collections in memory
        self.collections = {}

        logger.info(f"Vector Store initialized at: {persist_directory}")

    def add_documents(self, session_id: str, documents: List[Document]):
        """Add documents to the vector store for a session."""
        try:
            collection_name = f"session_{session_id}"

            # Delete existing collection if already present
            if collection_name in self.collections:
                self.client.delete_collection(collection_name)

            # Create and persist the collection
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=collection_name,
                persist_directory=self.persist_directory,
                client=self.client,
            )

            self.collections[collection_name] = vectorstore
            logger.info(f" Added {len(documents)} docs to collection '{collection_name}'")

        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    def similarity_search(self, session_id: str, query: str, k: int = 5) -> List[Document]:
        """Perform a similarity search."""
        try:
            collection_name = f"session_{session_id}"

            if collection_name not in self.collections:
                vectorstore = Chroma(
                    collection_name=collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory,
                    client=self.client,
                )
                self.collections[collection_name] = vectorstore
            else:
                vectorstore = self.collections[collection_name]

            results = vectorstore.similarity_search(query, k=k)
            logger.info(f" Found {len(results)} similar docs for query.")
            return results

        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []

    def similarity_search_with_score(
        self, session_id: str, query: str, k: int = 5
    ) -> List[tuple]:
        """Search for similar documents with relevance scores."""
        try:
            collection_name = f"session_{session_id}"

            if collection_name not in self.collections:
                vectorstore = Chroma(
                    collection_name=collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory,
                    client=self.client,
                )
                self.collections[collection_name] = vectorstore
            else:
                vectorstore = self.collections[collection_name]

            results = vectorstore.similarity_search_with_score(query, k=k)
            return results

        except Exception as e:
            logger.error(f"Error in similarity search with score: {str(e)}")
            return []

    def get_collection_count(self, session_id: str) -> int:
        """Get the number of documents in a session collection."""
        try:
            collection_name = f"session_{session_id}"
            collection = self.client.get_collection(collection_name)
            return collection.count()
        except Exception as e:
            logger.warning(f"Error getting collection count: {str(e)}")
            return 0

    def delete_collection(self, session_id: str):
        """Delete a session collection."""
        try:
            collection_name = f"session_{session_id}"

            if collection_name in self.collections:
                del self.collections[collection_name]

            self.client.delete_collection(collection_name)
            logger.info(f" Deleted collection: {collection_name}")

        except Exception as e:
            logger.warning(f"Error deleting collection: {str(e)}")

    def list_collections(self) -> List[str]:
        """List all available collections."""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
