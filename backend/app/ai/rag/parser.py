"""Robust document parsing for PDF / DOCX / TXT / CSV uploads."""

from __future__ import annotations

import io
import logging
from typing import Tuple

logger = logging.getLogger("aegis.ai.rag.parser")


def extract_text(filename: str, data: bytes) -> Tuple[str, str]:
    """Return (text, mime_type) for an uploaded file.

    Each parser is wrapped in a try/except so a broken upload never
    crashes the request — the user just gets ``""`` and the caller can
    decide what to do.
    """
    lower = (filename or "").lower()

    if lower.endswith(".pdf"):
        return _parse_pdf(data), "application/pdf"
    if lower.endswith(".docx"):
        return _parse_docx(data), (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    if lower.endswith(".csv"):
        return _parse_text(data), "text/csv"
    if lower.endswith((".txt", ".md", ".log")):
        return _parse_text(data), "text/plain"

    # Fallback — best-effort utf-8.
    return _parse_text(data), "application/octet-stream"


def _parse_text(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _parse_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as e:  # noqa: BLE001
        logger.warning("PDF parse failed: %s", e)
        return ""


def _parse_docx(data: bytes) -> str:
    try:
        import docx  # type: ignore

        document = docx.Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in document.paragraphs if p.text.strip())
    except Exception as e:  # noqa: BLE001
        logger.warning("DOCX parse failed: %s", e)
        return ""
