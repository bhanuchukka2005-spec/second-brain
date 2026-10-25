FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the embedding model at build time so the first upload doesn't
# have to fetch ~80MB at runtime.
RUN python -c "from chromadb.utils import embedding_functions; embedding_functions.DefaultEmbeddingFunction()(['warmup'])"

COPY . .

EXPOSE 8000

CMD sh -c "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"