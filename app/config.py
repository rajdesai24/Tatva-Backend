# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    MODEL_NAME: str = "gemini-2.5-flash"
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 8000
    CALIBRATION_TEMPERATURE: float = 1.45
    HOST: str = "0.0.0.0"  # Add this
    PORT: int = 8000        # Add this
    TAVILY_API_KEY:str ="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"
    class Config:
        env_file = ".env"
        extra = "ignore"  # Add this to ignore extra fields

@lru_cache()
def get_settings():
    return Settings()