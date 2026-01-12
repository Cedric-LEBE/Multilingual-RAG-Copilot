from __future__ import annotations

import os

import mlflow
import streamlit as st


def _setup() -> None:
    uri = st.secrets.get("MLFLOW_TRACKING_URI") or os.getenv("MLFLOW_TRACKING_URI")
    exp = st.secrets.get("MLFLOW_EXPERIMENT") or os.getenv("MLFLOW_EXPERIMENT") or "multilingual-rag-copilot"
    if uri:
        mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(exp)


def mlflow_log_index(doc_count: int, chunk_count: int, embedding_model: str, elapsed_s: float) -> None:
    _setup()
    with mlflow.start_run(run_name="index"):
        mlflow.log_param("embedding_model", embedding_model)
        mlflow.log_metric("doc_count", doc_count)
        mlflow.log_metric("chunk_count", chunk_count)
        mlflow.log_metric("index_elapsed_s", elapsed_s)


def mlflow_log_chat(backend: str, model: str, top_k: int, latency_s: float, retrieved: int) -> None:
    _setup()
    with mlflow.start_run(run_name="chat", nested=True):
        mlflow.log_param("backend", backend)
        mlflow.log_param("model", model)
        mlflow.log_param("top_k", top_k)
        mlflow.log_metric("latency_s", latency_s)
        mlflow.log_metric("retrieved_chunks", retrieved)
