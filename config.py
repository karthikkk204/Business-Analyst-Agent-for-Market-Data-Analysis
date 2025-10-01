"""Configuration settings for CrewInsight MVP."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    
    # API Authentication
    api_key: str = "crewinsight-mvp-2024"
    
    # Data Source API Keys
    alpha_vantage_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Rate Limiting
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
