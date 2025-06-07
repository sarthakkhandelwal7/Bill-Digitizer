from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, Union

class Settings(BaseSettings):
    """Application settings."""
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bill Digitizer API"
    
    # Google Gemini API
    GEMINI_API_KEY: str
    
    # Model settings
    MODEL_NAME: str = "gemini-2.0-flash-lite"
    
    # Authentication settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 24*60*7

    
    # OAuth settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Database settings
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "bill_digitizer_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None # Assembled from components

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL: # Construct DATABASE_URL if not explicitly set
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings() 