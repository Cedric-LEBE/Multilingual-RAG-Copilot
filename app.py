from __future__ import annotations

import time
from pathlib import Path

import streamlit as st

from src.mrc.auth import require_login
from src.mrc.ingest import load_uploaded_files, load_corpus_folder, chunk_documents
from src.mrc.store import rebuild_store, clear_store, retrieve
from src.mrc.llm import generate_answer
from src.mrc.telemetry import mlflow_log_chat, mlflow_log_index


st.set_page_config(page_title="Multilingual RAG Copilot", page_icon="🌍", layout="wide")

require_login()

st.title("🌍 Multilingual RAG Copilot")
st.caption("Upload documents → build index → ask questions (answers cite sources).")

with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("LLM backend")
    backend = st.selectbox("Backend", ["groq", "ollama"], index=0)
    groq_model = st.text_input("Groq model", value="llama-3.1-8b-instant")
    ollama_base_url = st.text_input("Ollama base URL", value="http://localhost:11434")
    ollama_model = st.text_input("Ollama model", value="llama3.1")

    st.subheader("Embeddings")
    embedding_model = st.text_input(
        "Embedding model",
        value="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )

    st.subheader("Chunking / Retrieval")
    chunk_size = st.slider("Chunk size (chars)", 400, 2000, 900, 50)
    overlap = st.slider("Overlap (chars)", 0, 400, 150, 10)
    top_k = st.slider("Top-k chunks", 2, 12, 6, 1)

    st.subheader("Observability (optional)")
    enable_mlflow = st.checkbox("Enable MLflow logging", value=False)

    st.divider()
    col1, col2 = st.columns(2)
    if col1.button("🧹 Clear index", use_container_width=True):
        clear_store()
        st.session_state.index_ready = False
        st.toast("Index cleared.")
    if col2.button("🔄 Reset chat", use_container_width=True):
        st.session_state.messages = []
        st.toast("Chat reset.")

    st.markdown("")  # small spacing before logout

    if st.button("🚪 Log out", use_container_width=True):
        for k in ["authed", "auth_user", "auth_pass"]:
            st.session_state.pop(k, None)
        st.rerun()

st.subheader("Upload documents")
uploads = st.file_uploader(
    "Accepted: PDF, TXT, MD, DOCX",
    type=["pdf", "txt", "md", "docx"],
    accept_multiple_files=True,
)

st.info(
    "Tip: For a deployed demo, you can also ship small sample docs in `corpus/` "
    "and click **Index corpus folder**."
)

btn_col1, btn_col2 = st.columns([1, 1])
index_msg = st.empty()

if "index_ready" not in st.session_state:
    st.session_state.index_ready = False
if "messages" not in st.session_state:
    st.session_state.messages = []

if btn_col1.button("📚 Build index from uploads", type="primary", use_container_width=True):
    if not uploads:
        st.warning("Upload at least one document.")
    else:
        t0 = time.time()
        docs = load_uploaded_files(uploads)
        chunks = chunk_documents(docs, chunk_size=chunk_size, overlap=overlap)
        rebuild_store(chunks, embedding_model=embedding_model)
        st.session_state.index_ready = True
        index_msg.success(f"Index ready: {len(chunks)} chunks.")
        if enable_mlflow:
            mlflow_log_index(
                doc_count=len(docs),
                chunk_count=len(chunks),
                embedding_model=embedding_model,
                elapsed_s=time.time() - t0,
            )

if btn_col2.button("📁 Index corpus folder", use_container_width=True):
    t0 = time.time()
    docs = load_corpus_folder(Path("corpus"))
    if not docs:
        st.warning("No documents found in ./corpus. Add files or use uploads.")
    else:
        chunks = chunk_documents(docs, chunk_size=chunk_size, overlap=overlap)
        rebuild_store(chunks, embedding_model=embedding_model)
        st.session_state.index_ready = True
        index_msg.success(f"Index ready: {len(chunks)} chunks.")
        if enable_mlflow:
            mlflow_log_index(
                doc_count=len(docs),
                chunk_count=len(chunks),
                embedding_model=embedding_model,
                elapsed_s=time.time() - t0,
            )

st.divider()
st.subheader("Ask questions")

if not st.session_state.index_ready:
    st.warning("Build an index first (uploads or corpus folder).")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("sources"):
            with st.expander("Sources"):
                for s in m["sources"]:
                    st.markdown(f"- **{s['source']}** (chunk {s['chunk_id']}, score={s['score']:.3f})")
                    st.caption(s["snippet"])

question = st.chat_input("Ask something about your documents…")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            t0 = time.time()
            contexts = retrieve(question, embedding_model=embedding_model, top_k=top_k)
            answer = generate_answer(
                backend=backend,
                question=question,
                contexts=contexts,
                groq_model=groq_model,
                ollama_base_url=ollama_base_url,
                ollama_model=ollama_model,
            )
            elapsed = time.time() - t0

            st.markdown(answer)
            sources = []
            with st.expander("Sources"):
                for c in contexts:
                    snippet = c["text"].strip().replace("\n", " ")
                    if len(snippet) > 260:
                        snippet = snippet[:260] + "…"
                    st.markdown(
                        f"- **{c['source']}** (chunk {c['chunk_id']}, score={c['score']:.3f})"
                    )
                    st.caption(snippet)
                    sources.append(
                        {
                            "source": c["source"],
                            "chunk_id": c["chunk_id"],
                            "score": c["score"],
                            "snippet": snippet,
                        }
                    )

            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )

            if enable_mlflow:
                mlflow_log_chat(
                    backend=backend,
                    model=groq_model if backend == "groq" else ollama_model,
                    top_k=top_k,
                    latency_s=elapsed,
                    retrieved=len(contexts),
                )

        except Exception as e:
            st.error(f"Error: {e}")
            if backend == "groq":
                st.info("Tip: set GROQ_API_KEY in Streamlit secrets.")
            else:
                st.info("Tip: ensure Ollama is running and the model is pulled.")
