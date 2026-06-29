FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY knowledge /app/knowledge

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./mcuverse.db
ENV FAISS_INDEX_PATH=/app/embeddings/faiss_index

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
