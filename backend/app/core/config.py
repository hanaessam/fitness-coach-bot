from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # API Info
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Fitness Coach Bot API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered fitness coaching with personalized workout and meal plans"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2000
    
    # Database Configuration
    CHROMA_PERSIST_DIR: str = "./data/processed/chroma_db"
    COLLECTION_NAME: str = "fitness_exercises"
    TOP_K_RESULTS: int = 5
    
    # Server Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]
    
    # Safety Constraints
    MIN_CALORIES: int = 1200
    MAX_CALORIES: int = 4000
    MAX_DEFICIT_PERCENT: float = 0.25
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def chroma_persist_path(self) -> Path:
        """Get absolute path for ChromaDB"""
        return Path(self.CHROMA_PERSIST_DIR).resolve()
    
    def validate_config(self) -> bool:
        """Validate critical configuration"""
        if not self.OPENAI_API_KEY or self.OPENAI_API_KEY == "your-key-here":
            raise ValueError("OPENAI_API_KEY not configured in .env file")
        return True

# Create global settings instance
settings = Settings()
settings.validate_config()