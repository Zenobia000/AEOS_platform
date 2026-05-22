"""file_parser 行為測試 — detect_format + parse_bytes (txt/md/pdf/docx)."""

from __future__ import annotations

import io

import pytest

from app.parsers import (
    ParseError,
    UnsupportedFormatError,
    detect_format,
    parse_bytes,
)

# ── detect_format ───────────────────────────────────


def test_detect_format_basic() -> None:
    assert detect_format("file.pdf") == "pdf"
    assert detect_format("file.docx") == "docx"
    assert detect_format("file.md") == "md"
    assert detect_format("file.markdown") == "md"
    assert detect_format("file.txt") == "txt"


def test_detect_format_case_insensitive() -> None:
    assert detect_format("FILE.PDF") == "pdf"
    assert detect_format("Notes.DocX") == "docx"


def test_detect_format_unsupported() -> None:
    with pytest.raises(UnsupportedFormatError):
        detect_format("file.csv")
    with pytest.raises(UnsupportedFormatError):
        detect_format("file")  # no extension


# ── parse_bytes: txt / md ──────────────────────────


def test_parse_txt_utf8() -> None:
    body = "退貨期限 7 天\n第二行".encode()
    out = parse_bytes(body, "faq.txt")
    assert "退貨期限" in out
    assert "第二行" in out


def test_parse_md_treated_as_text() -> None:
    body = "# 標題\n\n內容".encode()
    out = parse_bytes(body, "notes.md")
    assert "標題" in out


def test_parse_txt_handles_bad_utf8() -> None:
    """有壞 byte 不應 raise；errors='replace' 用替代字元."""
    body = b"hello\xff\xfeworld"
    out = parse_bytes(body, "x.txt")
    assert "hello" in out and "world" in out


# ── parse_bytes: PDF ───────────────────────────────


def _build_minimal_pdf(text: str = "hello AEOS") -> bytes:
    """用 pypdf 寫一個最小 PDF 給測試用."""
    from pypdf import PdfWriter

    # pypdf 無方便的純文字寫入 API；用 reportlab？避免新增 dep。
    # 改：用一個預先 embed 的最簡 PDF 並寫入 text — 不容易。
    # 折衷：寫一個空白頁 PDF；text extract 會回 ""，本檔仍能驗證 parser 不 crash
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_parse_pdf_blank_no_crash() -> None:
    """空白 PDF 不應 raise；回空 string."""
    data = _build_minimal_pdf()
    out = parse_bytes(data, "blank.pdf")
    # blank page 可能回空或極短；不該 raise
    assert isinstance(out, str)


def test_parse_pdf_corrupt_raises() -> None:
    with pytest.raises(ParseError):
        parse_bytes(b"not a pdf", "bad.pdf")


# ── parse_bytes: DOCX ──────────────────────────────


def _build_docx(paragraphs: list[str]) -> bytes:
    from docx import Document

    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_parse_docx_basic() -> None:
    data = _build_docx(["第一段：營業時間", "週一到週五 9~18 點"])
    out = parse_bytes(data, "hours.docx")
    assert "營業時間" in out
    assert "週一到週五" in out


def test_parse_docx_corrupt_raises() -> None:
    with pytest.raises(ParseError):
        parse_bytes(b"not a docx", "bad.docx")


# ── unsupported format propagation ─────────────────


def test_parse_unsupported_propagates() -> None:
    with pytest.raises(UnsupportedFormatError):
        parse_bytes(b"x", "data.csv")
