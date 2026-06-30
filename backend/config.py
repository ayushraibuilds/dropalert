from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Redis/Upstash Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Notification Services
    TELEGRAM_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None  # Admin notifications
    RESEND_API_KEY: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None

    # Web Push VAPID Configuration
    VAPID_PUBLIC_KEY: Optional[str] = None
    VAPID_PRIVATE_KEY: Optional[str] = None
    VAPID_CLAIM_EMAIL: str = "mailto:admin@dropalert.com"

    # Affiliate Tags
    AMAZON_AFFILIATE_TAG: Optional[str] = None
    FLIPKART_AFFILIATE_ID: Optional[str] = None

    # Scraper & Proxy Settings
    SCRAPER_INTERVAL_MINUTES: int = 5
    SCRAPER_PROXY_URL: Optional[str] = None  # ScraperAPI or residential proxies

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
