from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "yojanasetu"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    enable_demo_data: bool = False
    enable_dev_case_access: bool = False
    dev_access_token: str = ""
    enable_ai: bool = False
    chroma_path: str = "./data/chroma"
    chroma_collection: str = "verified_schemes_v1"
    embedding_provider: Literal["onnx", "ollama"] = "onnx"
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_provider: Literal["none", "ollama", "openai_compatible"] = "none"
    llm_model: str = "qwen2.5:3b"
    model_base_url: str = "http://127.0.0.1:11434"
    model_api_key: str = ""
    model_timeout_seconds: float = Field(default=45, ge=1, le=300)
    ai_timeout_seconds: float = Field(default=90, ge=1, le=600)
    retrieval_top_k: int = Field(default=8, ge=1, le=30)
    retrieval_max_distance: float = Field(default=0.65, ge=0, le=2)
    source_max_age_days: int = Field(default=365, ge=1, le=3650)
    ai_requests_per_minute: int = Field(default=10, ge=1, le=1000)
    conversation_ttl_hours: int = Field(default=24, ge=1, le=168)
    ingestion_max_bytes: int = Field(default=15_000_000, ge=1024, le=50_000_000)
    ingestion_max_pages: int = Field(default=150, ge=1, le=500)
    session_hours: int = Field(default=8, ge=1, le=24)
    login_attempts_per_minute: int = Field(default=10, ge=1, le=100)
    document_storage_path: str = "./data/private-documents"
    document_max_bytes: int = Field(default=10_000_000, ge=1024, le=20_000_000)
    document_retention_days: int = Field(default=30, ge=1, le=365)
    closed_case_retention_days: int = Field(default=180, ge=1, le=3650)
    enable_document_ocr: bool = False
    follow_up_interval_hours: int = Field(default=24, ge=1, le=168)
    escalation_inactivity_days: int = Field(default=7, ge=1, le=365)
    document_review_escalation_hours: int = Field(default=48, ge=1, le=720)
    missing_document_reminder_limit: int = Field(default=3, ge=1, le=20)
    escalation_reopen_hours: int = Field(default=24, ge=1, le=168)
    seva_notification_interval_hours: int = Field(default=1, ge=1, le=24)
    seva_retention_days: int = Field(default=180, ge=1, le=3650)
