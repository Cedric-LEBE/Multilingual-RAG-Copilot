from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from pypdf import PdfReader


@dataclass
class RawDoc:
    source: str
    text: str


def _clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = "\n".join([line.strip() for line in text.splitlines()])
    return "\n".join([line for line in text.splitlines() if line]).strip()


def _read_pdf(b: bytes, source: str) -> RawDoc:
    reader = PdfReader(BytesIO(b))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return RawDoc(source=source, text=_clean("\n".join(pages)))


def _read_txt(b: bytes, source: str) -> RawDoc:
    try:
        text = b.decode("utf-8")
    except UnicodeDecodeError:
        text = b.decode("latin-1", errors="ignore")
    return RawDoc(source=source, text=_clean(text))


def _read_md(b: bytes, source: str) -> RawDoc:
    return _read_txt(b, source)


def _read_docx(b: bytes, source: str) -> RawDoc:
    doc = DocxDocument(BytesIO(b))
    paras = [p.text for p in doc.paragraphs if p.text]
    return RawDoc(source=source, text=_clean("\n".join(paras)))


def _read_html(b: bytes, source: str) -> RawDoc:
    html = b.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    return RawDoc(source=source, text=_clean(soup.get_text(" ")))


def load_uploaded_files(files) -> List[RawDoc]:
    docs: List[RawDoc] = []
    for uf in files:
        name = uf.name
        suffix = Path(name).suffix.lower()
        b = uf.getvalue()

        if suffix == ".pdf":
            docs.append(_read_pdf(b, name))
        elif suffix == ".txt":
            docs.append(_read_txt(b, name))
        elif suffix == ".md":
            docs.append(_read_md(b, name))
        elif suffix == ".docx":
            docs.append(_read_docx(b, name))
        elif suffix in {".html", ".htm"}:
            docs.append(_read_html(b, name))
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    return [d for d in docs if d.text]


def load_corpus_folder(folder: Path) -> List[RawDoc]:
    if not folder.exists():
        return []
    docs: List[RawDoc] = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".pdf", ".txt", ".md", ".docx", ".html", ".htm"}:
            continue
        b = path.read_bytes()
        # fake UploadedFile-like object
        uf = type("UF", (), {"name": path.name, "getvalue": lambda self=b: self})()
        docs.extend(load_uploaded_files([uf]))
    return docs


def chunk_documents(docs: List[RawDoc], chunk_size: int = 900, overlap: int = 150):
    chunks = []
    for d in docs:
        text = d.text
        if len(text) <= chunk_size:
            chunks.append({"text": text, "source": d.source, "chunk_id": 0})
            continue
        start = 0
        cid = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append({"text": text[start:end], "source": d.source, "chunk_id": cid})
            cid += 1
            if end >= len(text):
                break
            start = max(0, end - overlap)
    return chunks
