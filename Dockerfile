# ── Stage 1: Builder — install all deps + download models ──────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system deps needed for ML packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Pre-download HuggingFace models into /models
ENV HF_HOME=/models
COPY scripts/download_models.py scripts/download_models.py
RUN python scripts/download_models.py

# ── Stage 2: Runtime — slim image with deps + models ───────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy pre-downloaded models
COPY --from=builder /models /models
ENV HF_HOME=/models

# Copy application code
COPY backend/ backend/
COPY pyproject.toml .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
