FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl docker.io && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY saas-devgen/executor-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities
COPY shared/ ./shared/

# Copy service files
COPY saas-devgen/executor-service/ .
RUN mkdir -p /app/logs

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
