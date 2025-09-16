# Use Python 3.10 as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Add shared directory to the container
COPY shared/ /app/shared/

# Set working directory for the service
WORKDIR /app/profile-service

# Copy requirements and install dependencies
COPY saas-devgen/profile-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY saas-devgen/profile-service/ .

# Create logs directory
RUN mkdir -p /app/logs

# Set Python path to include /app for shared module
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose port
EXPOSE 8007

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
