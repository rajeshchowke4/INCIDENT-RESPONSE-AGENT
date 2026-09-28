import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings:
    # Hindsight Memory Configuration
    HINDSIGHT_API_KEY: str = os.getenv("HINDSIGHT_API_KEY", "").strip()
    HINDSIGHT_BASE_URL: str = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").strip()
    HINDSIGHT_BANK_ID: str = os.getenv("HINDSIGHT_BANK_ID", "sre-production-incidents").strip()
    
    # LLM Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    
    # Server
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    @classmethod
    def is_hindsight_live(cls) -> bool:
        return bool(cls.HINDSIGHT_API_KEY)

    @classmethod
    def is_llm_live(cls) -> bool:
        return bool(cls.GROQ_API_KEY or cls.GEMINI_API_KEY)

settings = Settings()
