from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    DATABASE_URL: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    JWT_SECRET: str = "change-me"
    # Token used to protect internal sync endpoints. Set in environment for production.
    INTERNAL_SYNC_TOKEN: Optional[str] = None

    # Use ConfigDict for pydantic v2 settings; ignore extra env vars and load .env
    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
