FROM python:3.11-slim

WORKDIR /app

# Copy only the auth-service requirements
COPY saas-devgen/auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only auth-service source code
COPY saas-devgen/auth-service/main.py .
COPY saas-devgen/auth-service/tests/ ./tests/

EXPOSE 8004

CMD ["python", "main.py"]
