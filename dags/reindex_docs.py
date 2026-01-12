from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="reindex_docs",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    description="Rebuild Chroma index from ./corpus daily",
) as dag:
    rebuild = BashOperator(
        task_id="rebuild_index",
        bash_command=(
            "cd /opt/airflow/project && "
            "python -m venv .venv && "
            ". .venv/bin/activate && "
            "pip install -U pip && "
            "pip install -e . && "
            "python -c \"from src.mrc.ingest import load_corpus_folder, chunk_documents; "
            "from src.mrc.store import rebuild_store; "
            "from pathlib import Path; "
            "docs=load_corpus_folder(Path('corpus')); "
            "chunks=chunk_documents(docs); "
            "rebuild_store(chunks, embedding_model='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'); "
            "print('indexed', len(chunks))\""
        ),
    )
