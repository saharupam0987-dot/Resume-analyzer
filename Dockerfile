# =============================================================================
# Production Multi-stage Dockerfile for FastAPI & Celery Worker
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — Compile and package Python wheels
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /install

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Pre-install lightweight CPU-only PyTorch to avoid downloading ~3.5GB of NVIDIA CUDA packages
RUN pip install --no-cache-dir --prefix=/install/deps torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .

ENV PYTHONPATH="/install/deps/lib/python3.11/site-packages:${PYTHONPATH}"

RUN pip install --no-cache-dir --prefix=/install/deps --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime — Minimal production runtime
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Install runtime dependencies:
# - curl: for healthcheck probes
# - libpq5: PostgreSQL C client library
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install/deps /usr/local

WORKDIR /app

# Copy application source modules
COPY api/ ./api/
COPY auth/ ./auth/
COPY config/ ./config/
COPY database/ ./database/
COPY evaluation/ ./evaluation/
COPY generation/ ./generation/
COPY pdf_processing/ ./pdf_processing/
COPY rag/ ./rag/
COPY storage/ ./storage/
COPY tasks/ ./tasks/
COPY utils/ ./utils/
COPY requirements.txt .

# Pre-download the sentence-transformer embedding model so the container is ready instantly
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Create dedicated non-root application user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

# Create persistent storage directories with safe full permissions for appuser
RUN mkdir -p /app/uploads /app/chroma_db && \
    chown -R appuser:appuser /app && \
    chmod -R 777 /app/uploads /app/chroma_db

USER appuser

EXPOSE 8000

# Default entrypoint runs FastAPI (Celery worker overrides command in docker-compose)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
