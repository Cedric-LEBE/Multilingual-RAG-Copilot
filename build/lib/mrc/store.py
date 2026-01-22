from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

STORAGE_DIR = Path("storage")
META_PATH = STORAGE_DIR / "chunks.json"


def _ensure_dirs() -> None:
    STORAGE_DIR.mkdir(exist_ok=True)


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def get_store():
    _ensure_dirs()
    client = chromadb.PersistentClient(
        path=str(STORAGE_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(name="docs")


def clear_store() -> None:
    if STORAGE_DIR.exists():
        client = chromadb.PersistentClient(
            path=str(STORAGE_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        try:
            client.delete_collection(name="docs")
        except Exception:
            pass
    if META_PATH.exists():
        META_PATH.unlink()


def rebuild_store(chunks: List[Dict[str, Any]], embedding_model: str) -> None:
    clear_store()
    col = get_store()
    model = SentenceTransformer(embedding_model)

    ids, documents, metadatas, embeddings = [], [], [], []
    for c in chunks:
        text = c["text"]
        cid = f"{c['source']}::{c['chunk_id']}::{_fingerprint(text)[:12]}"
        ids.append(cid)
        documents.append(text)
        metadatas.append({"source": c["source"], "chunk_id": int(c["chunk_id"])})
        embeddings.append(model.encode(text, normalize_embeddings=True).tolist())

    col.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    META_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")


def retrieve(query: str, embedding_model: str, top_k: int = 6):
    col = get_store()
    model = SentenceTransformer(embedding_model)
    q = model.encode(query, normalize_embeddings=True).tolist()

    res = col.query(
        query_embeddings=[q],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        score = 1.0 - float(dist)
        out.append(
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "chunk_id": int(meta.get("chunk_id", -1)),
                "score": score,
            }
        )
    return out
