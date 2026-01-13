# Multilingual-Rag-copilot 🌍📚

A **multilingual RAG (Retrieval-Augmented Generation) app** that lets users upload (or mount) documents and ask questions **grounded in those documents**, with **citations**.

This version is designed to be **deployable with a public URL** (e.g., Streamlit Community Cloud) by using an **internet-accessible LLM backend** (Groq API). It also supports an optional local backend (Ollama).

## What it does
- Upload multiple documents (**PDF, TXT, MD, DOCX**)
- Build a local vector index (ChromaDB)
- Ask questions in **any language**
- Answer in the **same language as the question**
- Show **sources** (document + chunk)

## Deployment (public URL)
Recommended: **Streamlit Community Cloud** + **Groq API key**.
- Store your `GROQ_API_KEY` using Streamlit secrets management. citeturn0search2
- Groq imposes rate limits depending on plan/tier. citeturn0search1

## Quickstart (local)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
streamlit run app.py
```

### Secrets (local)
Create `.streamlit/secrets.toml` from the template:
```toml
GROQ_API_KEY = "..."
AUTH_USERNAME = "admin"
AUTH_PASSWORD_HASH = "$2b$12$..."
```

Generate a bcrypt hash:
```bash
python scripts/hash_password.py "your_password"
```

## Optional: Airflow (local, for scheduled re-indexing)
A sample Airflow DAG is provided in `dags/reindex_docs.py` and a `docker-compose.airflow.yml` for local runs.
Airflow is **not required** for the deployed demo URL.

## Optional: MLflow
MLflow logging is included for:
- indexing runs (chunks, doc count, embedding model)
- chat usage metrics (latency, retrieved chunks)

Enable by setting `MLFLOW_TRACKING_URI` (local) and `MLFLOW_EXPERIMENT` in secrets/env.

## Project structure
```
multilingual-rag-copilot/
├─ app.py
├─ src/mrc/              # core modules
├─ corpus/               # optional mounted docs for demo (gitignored or small samples)
├─ storage/              # Chroma persistence (gitignored)
├─ dags/                 # optional Airflow DAGs
├─ scripts/              # helper scripts
└─ pyproject.toml
```

## Notes & limitations
- Images/video/audio are not supported in this version (text-only extraction).
- For a completely offline demo, use the Ollama backend locally.

## License
Educational use.
