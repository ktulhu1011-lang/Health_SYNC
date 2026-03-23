from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    garmin_encryption_key: str = ""
    anthropic_api_key: str = ""
    database_url: str = "postgresql://healthsync:healthsync@db:5432/healthsync"
    jwt_secret: str = "change_me_in_production"
    jwt_expire_minutes: int = 10080  # 7 days
    frontend_url: str = "http://localhost:3000"
    garmin_sync_hour: int = 10
    weekly_insight_day: str = "sunday"
    optional_morning_reminder: str = "08:00"
    user1_username: str = "user1"
    user1_password: str = "change_me_1"
    user1_telegram_id: Optional[int] = None
    user2_username: str = "user2"
    user2_password: str = "change_me_2"
    user2_telegram_id: Optional[int] = None

    class Config:
        env_file = ".env"


settings = Settings()
