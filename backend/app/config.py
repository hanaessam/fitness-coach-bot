"""
Configuration with RAG settings
"""
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2000
    
    # RAG Configuration
    CHROMA_PERSIST_DIR: str = "./data/processed/chroma_db"
    COLLECTION_NAME: str = "fitness_exercises"
    TOP_K_RESULTS: int = 5
    
    # API Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    class Config:
        env_file = "../.env"
        case_sensitive = True
        env_file_encoding = 'utf-8'
        extra = 'ignore'
    
    @property
    def chroma_path(self) -> Path:
        """Get absolute path for ChromaDB"""
        # Go up from backend/ to project root, then to data/
        backend_dir = Path(__file__).parent.parent
        project_root = backend_dir.parent
        return project_root / "data" / "processed" / "chroma_db"
    
    def validate_openai_key(self) -> bool:
        """Validate OpenAI API key"""
        if not self.OPENAI_API_KEY or self.OPENAI_API_KEY.startswith("sk-proj-your"):
            raise ValueError("OPENAI_API_KEY not configured")
        return True

# Create global settings
settings = Settings()

# Validate on startup
try:
    settings.validate_openai_key()
    print(f"✓ Config loaded - Model: {settings.MODEL_NAME}")
except ValueError as e:
    print(f"⚠ Warning: {e}")
