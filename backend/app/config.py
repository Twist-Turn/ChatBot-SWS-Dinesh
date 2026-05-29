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


settings = Settings()
