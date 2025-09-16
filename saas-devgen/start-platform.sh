#!/bin/bash

# AI Software Generator - Docker-Based Startup Script
# This script starts all services using Docker Compose

set -e

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  No .env file found. Some services may not work properly."
fi

echo " Starting AI Software Generator Platform with Docker"
echo "===================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
cd infra
docker compose -f docker-compose-full.yml down --remove-orphans 2>/dev/null || true

# Build and start all services
echo "🏗️  Building and starting all services..."
docker compose -f docker-compose-full.yml up --build -d

echo "⏳ Waiting for services to start..."
sleep 60

# Function to check service health
check_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo "🔍 Checking $service_name on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
            echo "✅ $service_name is ready"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ $service_name failed to start"
            docker compose -f docker-compose-full.yml logs $service_name
            return 1
        fi
        
        echo "⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
}

echo "� Checking service health..."

# Check infrastructure services first
sleep 30

# Check application services
check_service "auth-service" 8001
check_service "orchestrator" 8002
check_service "codegen-service" 8003
check_service "executor-service" 8004
check_service "storage-service" 8005
check_service "audit-service" 8006
check_service "api-gateway" 9090

echo ""
echo "🎉 AI Software Generator Platform is ready!"
echo "=========================================="
echo ""
echo "📋 Service URLs:"
echo "  🌐 API Gateway:        http://localhost:9090"
echo "  🔐 Auth Service:       http://localhost:8001"
echo "  🎯 Orchestrator:       http://localhost:8002"
echo "  🛠️  Codegen Service:    http://localhost:8003"
echo "  ⚡ Executor Service:   http://localhost:8004"
echo "  💾 Storage Service:    http://localhost:8005"
echo "  📊 Audit Service:      http://localhost:8006"
echo ""
echo "🏗️  Infrastructure:"
echo "  🐘 PostgreSQL:         localhost:5432"
echo "  🗄️  MinIO:              http://localhost:9001 (admin/admin123)"
echo "  🔐 Keycloak:           http://localhost:8080 (admin/admin)"
echo "  📊 Loki:               http://localhost:3100"
echo ""
echo "📖 API Documentation:   http://localhost:9090/docs"
echo "🩺 Health Check:        http://localhost:9090/health"
echo ""
echo "� Container Management:"
echo "  View logs:    docker compose -f infra/docker-compose-full.yml logs -f [service-name]"
echo "  Stop all:     docker compose -f infra/docker-compose-full.yml down"
echo "  Restart:      docker compose -f infra/docker-compose-full.yml restart [service-name]"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    cd infra && docker compose -f docker-compose-full.yml down
    echo "✅ All services stopped"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Keep the script running
echo ""
echo "Press Ctrl+C to stop all services"
echo "Platform is running in Docker containers..."
wait
