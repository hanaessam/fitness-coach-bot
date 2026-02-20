#!/bin/bash

# Run data ingestion if ChromaDB is empty
if [ ! -d "/app/chroma_db/chroma.sqlite3" ]; then
    echo "Running data ingestion..."
    python -m app.rag.ingest
    echo "Ingestion complete."
fi

# Start FastAPI in the background on port 8000
uvicorn app.api:app --host 0.0.0.0 --port 8000 &

# Wait for FastAPI to be ready
sleep 3

# Start Streamlit on port 7860 (required by HF Spaces)
streamlit run app/main.py \
    --server.port 7860 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false