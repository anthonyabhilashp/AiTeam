FROM python:3.11-slim

WORKDIR /app

# Install required packages
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY saas-devgen/db-init/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities and initialization script
COPY shared/ ./shared/
COPY saas-devgen/db-init/init_db.py .
COPY saas-devgen/db-init/migrations/ ./migrations/

# Run initialization
CMD ["python", "init_db.py"]
