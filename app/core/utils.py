from pathlib import Path
import unicodedata
from typing import Set

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


# ── Multilingual script detection ───────────────────────────────────────────
# Unicode block ranges for commonly used scripts.
# Reference: https://www.unicode.org/charts/
_SCRIPT_RANGES = {
    "devanagari":  ('\u0900', '\u097F'),   # Hindi, Marathi, Sanskrit, Nepali
    "arabic":      ('\u0600', '\u06FF'),   # Arabic, Urdu, Persian, Pashto
    "bengali":     ('\u0980', '\u09FF'),   # Bengali, Assamese
    "gurmukhi":    ('\u0A00', '\u0A7F'),   # Punjabi
    "gujarati":    ('\u0A80', '\u0AFF'),   # Gujarati
    "tamil":       ('\u0B80', '\u0BFF'),   # Tamil
    "telugu":      ('\u0C00', '\u0C7F'),   # Telugu
    "kannada":     ('\u0C80', '\u0CFF'),   # Kannada
    "malayalam":   ('\u0D00', '\u0D7F'),   # Malayalam
    "thai":        ('\u0E00', '\u0E7F'),   # Thai
    "cjk":         ('\u4E00', '\u9FFF'),   # Chinese (CJK Unified Ideographs)
    "hangul":      ('\uAC00', '\uD7AF'),   # Korean (Hangul Syllables)
    "hiragana":    ('\u3040', '\u309F'),   # Japanese Hiragana
    "katakana":    ('\u30A0', '\u30FF'),   # Japanese Katakana
    "cyrillic":    ('\u0400', '\u04FF'),   # Russian, Ukrainian, Bulgarian, etc.
    "georgian":    ('\u10A0', '\u10FF'),   # Georgian
    "armenian":    ('\u0530', '\u058F'),   # Armenian
    "ethiopic":    ('\u1200', '\u137F'),   # Amharic, Tigrinya, etc.
    "khmer":       ('\u1780', '\u17FF'),   # Khmer (Cambodian)
    "myanmar":     ('\u1000', '\u109F'),   # Myanmar (Burmese)
    "sinhala":     ('\u0D80', '\u0DFF'),   # Sinhala
    "lao":         ('\u0E80', '\u0EFF'),   # Lao
    "tibetan":     ('\u0F00', '\u0FFF'),   # Tibetan
    "odia":        ('\u0B00', '\u0B7F'),   # Odia (Oriya)
}

# Human-readable labels for the script-preservation prompt note
_SCRIPT_LABELS = {
    "devanagari":  "Devanagari (Hindi/Marathi/Sanskrit/Nepali)",
    "arabic":      "Arabic / Urdu / Persian",
    "bengali":     "Bengali",
    "gurmukhi":    "Gurmukhi (Punjabi)",
    "gujarati":    "Gujarati",
    "tamil":       "Tamil",
    "telugu":      "Telugu",
    "kannada":     "Kannada",
    "malayalam":   "Malayalam",
    "thai":        "Thai",
    "cjk":         "Chinese (CJK)",
    "hangul":      "Korean (Hangul)",
    "hiragana":    "Japanese (Hiragana)",
    "katakana":    "Japanese (Katakana)",
    "cyrillic":    "Cyrillic (Russian/Ukrainian/Bulgarian)",
    "georgian":    "Georgian",
    "armenian":    "Armenian",
    "ethiopic":    "Ethiopic (Amharic/Tigrinya)",
    "khmer":       "Khmer",
    "myanmar":     "Myanmar (Burmese)",
    "sinhala":     "Sinhala",
    "lao":         "Lao",
    "tibetan":     "Tibetan",
    "odia":        "Odia",
}


def detect_scripts(text: str) -> Set[str]:
    """Return the set of non-Latin script names found in *text*.

    Only scripts defined in _SCRIPT_RANGES are detected.
    Returns an empty set for pure-ASCII / Latin-only text.
    """
    found: Set[str] = set()
    if not text:
        return found

    for ch in text:
        for name, (lo, hi) in _SCRIPT_RANGES.items():
            if name in found:
                continue
            if lo <= ch <= hi:
                found.add(name)
        # Fast exit once we've matched everything
        if len(found) == len(_SCRIPT_RANGES):
            break
    return found


def has_non_latin(text: str) -> bool:
    """Return True if *text* contains any non-Latin script characters."""
    return bool(detect_scripts(text))


def script_preservation_note(text: str) -> str:
    """Build a prompt-ready note listing which scripts must be preserved verbatim.

    Returns an empty string if only Latin/ASCII text is detected.
    """
    scripts = detect_scripts(text)
    if not scripts:
        return ""

    labels = sorted(_SCRIPT_LABELS.get(s, s) for s in scripts)
    listing = ", ".join(labels)
    return (
        f"\nSCRIPT NOTE: The Context contains text in: {listing}. "
        "When copying text into the evidence block, reproduce it in its original "
        "script exactly — never romanise, transliterate, or translate the cited text."
    )
