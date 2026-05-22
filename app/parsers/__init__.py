"""File parsers — 從 bytes / path 取出 text.

依 PRD-001 §5.1 F-KB-01: PDF / DOCX / MD / TXT；單檔 ≤ 20MB.
Phase 1 簡化：URL fetch (F-KB-02) 留後續。
"""

from app.parsers.file_parser import (
    ParseError,
    UnsupportedFormatError,
    detect_format,
    parse_bytes,
)

__all__ = ["ParseError", "UnsupportedFormatError", "detect_format", "parse_bytes"]
