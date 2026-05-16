import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_password: str
    db_path: str
    openrouter_api_key: str
    session_secret: str



def get_settings() -> Settings:
    app_password = os.getenv("APP_PASSWORD", "")
    return Settings(
        app_password=app_password,
        db_path=os.getenv("DB_PATH", "data/app.db"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        session_secret=os.getenv("SESSION_SECRET", app_password or "suibi-dev-secret"),
    )
