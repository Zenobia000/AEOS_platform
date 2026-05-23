"""File parser dispatch — 依 filename 副檔名選 parser → 回 text.

依 PRD-001 §5.1 F-KB-01:
- pdf: pypdf.PdfReader
- docx: python-docx
- md / markdown: utf-8 decode（markdown 字面 = 純文字）
- txt: utf-8 decode

任意 raise → ParseError；不支援格式 → UnsupportedFormatError.
"""

from __future__ import annotations

import io
from pathlib import PurePath
from typing import Literal

SupportedFormat = Literal["pdf", "docx", "md", "txt"]

SUPPORTED_EXTENSIONS: dict[str, SupportedFormat] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".md": "md",
    ".markdown": "md",
    ".txt": "txt",
}


class ParseError(RuntimeError):
    """parse 解析失敗（檔案損壞、編碼錯誤等）."""


class UnsupportedFormatError(ValueError):
    """副檔名不在支援清單."""


def detect_format(filename: str) -> SupportedFormat:
    ext = PurePath(filename).suffix.lower()
    fmt = SUPPORTED_EXTENSIONS.get(ext)
    if fmt is None:
        raise UnsupportedFormatError(
            f"unsupported extension: {ext!r} (supported: {sorted(SUPPORTED_EXTENSIONS)})"
        )
    return fmt


def parse_bytes(data: bytes, filename: str) -> str:
    """從 bytes + filename → text (UTF-8 string)."""
    fmt = detect_format(filename)
    try:
        if fmt == "pdf":
            return _parse_pdf(data)
        if fmt == "docx":
            return _parse_docx(data)
        # md / txt — 直接 decode
        return data.decode("utf-8", errors="replace")
    except UnsupportedFormatError:
        raise
    except Exception as exc:
        raise ParseError(f"failed to parse {fmt} ({filename}): {exc}") from exc


def _parse_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)
    return "\n\n".join(parts)


def _parse_docx(data: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text)
