FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install Python dependencies
COPY saas-devgen/profile-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY saas-devgen/profile-service/main.py .

# Copy tests directory
COPY saas-devgen/profile-service/tests/ ./tests/

# Expose port for FastAPI
EXPOSE 8005

# Run the FastAPI application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
