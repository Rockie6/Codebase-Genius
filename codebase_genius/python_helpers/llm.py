"""LLM integration stubs for README summarization.
Uses Gemini if GEMINI_API_KEY and USE_LLM=1 are set; falls back otherwise.
"""
from __future__ import annotations
import os
from typing import Optional

try:
    import google.generativeai as genai  # type: ignore
    HAS_GEMINI = True
except Exception:  # pragma: no cover
    HAS_GEMINI = False

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def _is_truthy(val: Optional[str]) -> bool:
    if val is None:
        return False
    return val.strip().lower() in {"1", "true", "yes", "on"}


def summarize_readme_llm(text: str, max_len: int = 500) -> str:
    """LLM summary (Gemini) or fallback to naive truncation."""
    if not text:
        return "No README content found."
    if not _is_truthy(os.getenv("USE_LLM")):
        return _fallback(text, max_len)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not HAS_GEMINI:
        return _fallback(text, max_len)
    try:
        genai.configure(api_key=api_key)
        prompt = (
            "Summarize the following project README into a concise overview (avoid marketing fluff).\n\n" + text[:6000]
        )
        model = genai.GenerativeModel(DEFAULT_MODEL)
        resp = model.generate_content(prompt)
        out = resp.text.strip() if hasattr(resp, "text") and resp.text else ""
        if not out:
            return _fallback(text, max_len)
        # Trim overly long response
        return out[:max_len] + ("..." if len(out) > max_len else "")
    except Exception:
        return _fallback(text, max_len)


def _fallback(text: str, max_len: int) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:max_len] + ("..." if len(cleaned) > max_len else "")
