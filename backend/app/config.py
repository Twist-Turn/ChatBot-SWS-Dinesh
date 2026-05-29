from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"

    chunk_size: int = 500
    chunk_overlap: int = 50
    retrieval_k: int = 5

    documents_dir: Path = REPO_DIR / "Documents"
    chroma_dir: Path = BACKEND_DIR / "chroma_db"
    chroma_collection: str = "sws_ai_docs"

    admin_api_key: str = ""
    rate_limit_chat: str = "20/minute"
    rate_limit_upload: str = "5/minute"
    max_upload_mb: int = 5

    # Supabase chat history (leave blank to disable persistence)
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_history_table: str = "chat_messages"
    chat_history_limit: int = 200


settings = Settings()
