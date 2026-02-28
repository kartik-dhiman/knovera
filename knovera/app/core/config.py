from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Knovera"
    app_env: str = "dev"

    data_dir: str = "./data"
    upload_dir: str = "./data/uploads"
    chroma_dir: str = "./data/chroma"
    sqlite_path: str = "./data/app.db"

    collection_name: str = "pdf_chunks"

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    chunk_size: int = 900
    chunk_overlap: int = 150

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b-instruct"

    retrieval_top_k: int = 3
    max_context_chars: int = 3500

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
