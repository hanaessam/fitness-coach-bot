import chromadb
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from typing import List, Dict, Optional
from pathlib import Path
import os

from backend.app.core.config import settings
from backend.app.utils.data_processor import ExerciseDataProcessor

class RAGService:
    """Retrieval-Augmented Generation service"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.vectorstore: Optional[Chroma] = None
        self.retriever = None
        self._is_initialized = False
    
    def build_vectorstore(self, csv_path: str):
        """Build ChromaDB from exercise dataset"""
        print(f"Processing exercise data from {csv_path}...")
        processor = ExerciseDataProcessor(csv_path)
        exercise_docs = processor.process()
        
        documents = [
            Document(
                page_content=doc['text'],
                metadata=doc['metadata']
            )
            for doc in exercise_docs
        ]
        
        print(f"Creating embeddings for {len(documents)} exercises...")
        
        # Ensure persist directory exists
        persist_dir = settings.chroma_persist_path
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=settings.COLLECTION_NAME,
            persist_directory=str(persist_dir)
        )
        
        print(f"Vectorstore created and persisted to {persist_dir}")
        
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": settings.TOP_K_RESULTS}
        )
        self._is_initialized = True
    
    def load_vectorstore(self):
        """Load existing ChromaDB vectorstore"""
        persist_dir = settings.chroma_persist_path
        
        if not persist_dir.exists():
            raise FileNotFoundError(
                f"Vectorstore not found at {persist_dir}. "
                "Run build_vectorstore first."
            )
        
        print(f"Loading vectorstore from {persist_dir}...")
        self.vectorstore = Chroma(
            collection_name=settings.COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(persist_dir)
        )
        
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": settings.TOP_K_RESULTS}
        )
        self._is_initialized = True
        print("Vectorstore loaded successfully")
    
    def search_exercises(
        self,
        query: str,
        k: int = None,
        filters: Dict = None
    ) -> List[Document]:
        """Search for relevant exercises"""
        if not self._is_initialized:
            raise RuntimeError("RAG service not initialized. Call load_vectorstore first.")
        
        search_kwargs = {"k": k or settings.TOP_K_RESULTS}
        if filters:
            search_kwargs["filter"] = filters
        
        results = self.vectorstore.similarity_search(query, **search_kwargs)
        
        return results
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._is_initialized

# Global RAG service instance
rag_service = RAGService()