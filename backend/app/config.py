"""
Configuration management with OpenAI settings
"""
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings loaded from .env"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    MODEL_NAME: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2000
    
    # API Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    class Config:
        env_file = "../.env"
        case_sensitive = True
        env_file_encoding = 'utf-8'
        extra = 'ignore'
    
    def validate_openai_key(self) -> bool:
        """Validate OpenAI API key is configured"""
        if not self.OPENAI_API_KEY or self.OPENAI_API_KEY.startswith("sk-proj-your"):
            raise ValueError(
                "OPENAI_API_KEY not configured. "
                "Get your key from https://platform.openai.com/api-keys"
            )
        return True

# Create global settings instance
settings = Settings()

# Validate on startup
try:
    settings.validate_openai_key()
    print(f"✓ Config loaded - Model: {settings.MODEL_NAME}")
except ValueError as e:
    print(f"⚠ Warning: {e}")
    print("  LLM features will not work until API key is configured")
