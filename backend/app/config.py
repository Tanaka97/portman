"""
Configuration file for the application.
Loads environment variables and provides settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # Supabase settings
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon key")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    
    # Configuration for pydantic-settings v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.
    Cached to avoid reading .env multiple times.
    """
    return Settings()


# Test if run directly
if __name__ == "__main__":
    try:
        settings = get_settings()
        print(f"✅ Config loaded successfully!")
        print(f"✅ Supabase URL: {settings.supabase_url}")
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ API will run on: {settings.api_host}:{settings.api_port}")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        print("\nTroubleshooting:")
        print("1. Check .env file exists in root folder")
        print("2. Check SUPABASE_URL and SUPABASE_KEY are set")
        print("3. Check .env file encoding is UTF-8 (not UTF-8 with BOM)")