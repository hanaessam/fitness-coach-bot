"""
RAG (Retrieval-Augmented Generation) Service
Handles exercise search using vector embeddings
"""

from langchain_chroma import Chroma  # ← UPDATED IMPORT
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from typing import List, Dict, Optional
from pathlib import Path

from app.config import settings
from app.utils.data_processor import ExerciseDataProcessor


class RAGService:
    """
    RAG service for exercise recommendations

    Uses ChromaDB for vector storage and OpenAI embeddings
    for semantic search
    """

    def __init__(self):
        """Initialize RAG service"""
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL, openai_api_key=settings.OPENAI_API_KEY
        )
        self.vectorstore: Optional[Chroma] = None
        self._is_initialized = False

    def build_vectorstore(self, csv_path: str):
        """
        Build vector database from CSV

        Args:
            csv_path: Path to exercise CSV file
        """
        print(f"\n{'='*60}")
        print("Building Exercise Vector Database")
        print(f"{'='*60}")

        # Process CSV data
        processor = ExerciseDataProcessor(csv_path)
        exercise_docs = processor.process()

        # Convert to LangChain Document format
        documents = [
            Document(page_content=doc["text"], metadata=doc["metadata"])
            for doc in exercise_docs
        ]

        print(f"\nCreating embeddings for {len(documents)} exercises...")
        print("(This may take a minute...)")

        # Ensure persist directory exists
        persist_dir = settings.chroma_path
        persist_dir.mkdir(parents=True, exist_ok=True)

        # Create ChromaDB vectorstore
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=settings.COLLECTION_NAME,
            persist_directory=str(persist_dir),
        )

        print(f"\n✓ Vectorstore created at: {persist_dir}")
        self._is_initialized = True

    def load_vectorstore(self):
        """Load existing vector database"""
        persist_dir = settings.chroma_path

        if not persist_dir.exists():
            raise FileNotFoundError(
                f"Vectorstore not found at {persist_dir}. "
                f"Run build_database.py first."
            )

        print(f"Loading vectorstore from {persist_dir}...")

        self.vectorstore = Chroma(
            collection_name=settings.COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(persist_dir),
        )

        self._is_initialized = True
        print("✓ Vectorstore loaded")

    def search_exercises(
        self, query: str, k: int = None, filters: Dict = None
    ) -> List[Document]:
        """
        Search for relevant exercises

        Args:
            query: Search query (e.g., "chest exercises for beginners")
            k: Number of results to return
            filters: Metadata filters (e.g., {"level": "beginner"})

        Returns:
            List of matching exercise documents
        """
        if not self._is_initialized:
            raise RuntimeError(
                "RAG service not initialized. Call load_vectorstore() first."
            )

        k = k or settings.TOP_K_RESULTS

        # Perform similarity search
        if filters:
            results = self.vectorstore.similarity_search(query, k=k, filter=filters)
        else:
            results = self.vectorstore.similarity_search(query, k=k)

        return results

    @property
    def is_initialized(self) -> bool:
        """Check if RAG service is ready"""
        return self._is_initialized


# Global RAG service instance
rag_service = RAGService()
