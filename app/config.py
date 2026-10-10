import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings:
    APP_NAME: str = os.getenv(
        "APP_NAME",
        "FitBuddy - AI Fitness Plan Generator"
    )

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./fitbuddy.db"
    )

    GEMINI_API_KEY: str = os.getenv(
        "GEMINI_API_KEY",
        ""
    )

    WORKOUT_MODEL: str = os.getenv(
        "WORKOUT_MODEL",
        "gemini-3.5-flash-lite"
    )

    TIP_MODEL: str = os.getenv(
        "TIP_MODEL",
        "gemini-3.5-flash-lite"
    )

    ADMIN_KEY: str = os.getenv(
        "ADMIN_KEY",
        "change-me"
    )

    DEBUG: bool = os.getenv(
        "DEBUG",
        "true"
    ).lower() == "true"


settings = Settings()