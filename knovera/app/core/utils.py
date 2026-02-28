from pathlib import Path
import unicodedata

from app.core.config import settings


def ensure_data_dirs() -> None:
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)


def normalize_text(text: str) -> str:
    """Return a normalized Unicode string (NFKC) suitable for indexing/querying."""
    if not text:
        return text
    return unicodedata.normalize('NFKC', text)
