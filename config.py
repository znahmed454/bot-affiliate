"""
Konfigurasi terpusat untuk bot
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # API Keys
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    KLING_API_KEY = os.getenv("KLING_API_KEY")
    KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY")
    RUNWAY_API_SECRET = os.getenv("RUNWAY_API_SECRET")

    # Model settings
    REPLICATE_IMAGE_MODEL = os.getenv(
        "REPLICATE_IMAGE_MODEL",
        "stability-ai/sdxl:39ed52f2319f9c1234d7be100898cbfad7a027a2ae0e73cad90cbcea5e72e8f"
    )
    IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", 1024))
    IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", 1024))
    VIDEO_DURATION = int(os.getenv("VIDEO_DURATION", 5))

    # Bot settings
    CAPTION_LANGUAGE = os.getenv("CAPTION_LANGUAGE", "indonesia")
    MAX_HISTORY = int(os.getenv("MAX_HISTORY", 10))
    TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def validate(cls):
        """Validasi konfigurasi wajib"""
        required = {
            "TELEGRAM_BOT_TOKEN": cls.TELEGRAM_BOT_TOKEN,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Variabel wajib tidak ditemukan: {', '.join(missing)}")

        if not any([cls.REPLICATE_API_TOKEN, cls.OPENAI_API_KEY]):
            raise ValueError("Minimal satu API gambar diperlukan: REPLICATE_API_TOKEN atau OPENAI_API_KEY")

        if not any([cls.ANTHROPIC_API_KEY, cls.OPENAI_API_KEY]):
            raise ValueError("Minimal satu API caption diperlukan: ANTHROPIC_API_KEY atau OPENAI_API_KEY")


config = Config()
