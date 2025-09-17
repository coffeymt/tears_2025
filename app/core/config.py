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
    # SMTP / email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    # From header (can include name). Example: "SBCC Tears <michael@sbcctears.com>"
    MAIL_FROM: Optional[str] = None
    # Reply-To header for broadcasts
    BROADCAST_REPLY_TO: Optional[str] = None

    # Use ConfigDict for pydantic v2 settings; ignore extra env vars and load .env
    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
