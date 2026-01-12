from __future__ import annotations

from typing import Dict, List

import requests
import streamlit as st
from groq import Groq


def _build_prompt(question: str, contexts: List[Dict]) -> str:
    ctx = "\n\n".join(
        [f"[Source: {c['source']} | chunk {c['chunk_id']}]\n{c['text']}" for c in contexts]
    )
    return f"""You are a helpful assistant. Answer using ONLY the provided context.
Rules:
- If the answer is not in the context, say you don't know and ask for more documents.
- Answer in the SAME language as the user's question.
- Provide a concise answer first, then bullet points if useful.

User question:
{question}

Context:
{ctx}
"""


def _groq_chat(model: str, prompt: str) -> str:
    api_key = st.secrets.get("GROQ_API_KEY") or ""
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY in Streamlit secrets.")
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def _ollama_generate(base_url: str, model: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/api/generate"
    r = requests.post(
        url,
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
        timeout=120,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Ollama error {r.status_code}: {r.text[:200]}")
    return (r.json().get("response") or "").strip()


def generate_answer(
    backend: str,
    question: str,
    contexts: List[Dict],
    groq_model: str,
    ollama_base_url: str,
    ollama_model: str,
) -> str:
    prompt = _build_prompt(question, contexts)
    if backend == "groq":
        return _groq_chat(groq_model, prompt)
    return _ollama_generate(ollama_base_url, ollama_model, prompt)
