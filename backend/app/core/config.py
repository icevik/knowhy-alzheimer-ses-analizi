from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://voiceanalyzer:voiceanalyzer_pass@postgres:5432/voiceanalyzer_db",
    )

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str | None = os.getenv("OPENAI_BASE_URL") or None
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
    openai_whisper_model: str = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
    openai_timeout_seconds: int = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "900"))

    # OpenRouter (AI Model Provider)
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_timeout_seconds: int = int(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "900"))

    upload_dir: str = "uploads"
    PROJECT_NAME: str = "KNOWHY Alzheimer Analiz"
    reports_dir: str = "reports"
    max_file_size: int = 25 * 1024 * 1024  # 25MB
    
    # JWT Authentication
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 saat
    
    # Email Webhook
    email_webhook_url: str = os.getenv("EMAIL_WEBHOOK_URL", "")
    
    # Rate Limiting
    login_max_attempts: int = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
    login_window_minutes: int = int(os.getenv("LOGIN_WINDOW_MINUTES", "15"))
    email_max_sends: int = int(os.getenv("EMAIL_MAX_SENDS", "3"))
    email_window_minutes: int = int(os.getenv("EMAIL_WINDOW_MINUTES", "60"))
    account_lock_minutes: int = int(os.getenv("ACCOUNT_LOCK_MINUTES", "60"))
    max_failed_attempts_before_lock: int = int(os.getenv("MAX_FAILED_ATTEMPTS_BEFORE_LOCK", "10"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()


