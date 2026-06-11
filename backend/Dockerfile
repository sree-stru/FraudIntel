# ── Stage 1: Install Python dependencies ──────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime image ────────────────────────────────────────
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g mongodb-mcp-server && \
    apt-get purge -y curl && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
WORKDIR /app
COPY backend/agent/ ./agent/
COPY backend/api/ ./api/
COPY frontend/ ./frontend/
COPY backend/data/ ./data/
EXPOSE 8080
ENV PORT=8080
CMD ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080"]

