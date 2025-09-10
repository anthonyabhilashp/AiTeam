#!/bin/bash

# AI Software Generator - Complete Startup Script
# This script starts all microservices for the AI Software Generator platform


set -e

# Auto-activate Python virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    # Try common venv locations
    if [ -d "../venv" ]; then
        echo "🔄 Activating Python virtual environment at ../venv"
        source ../venv/bin/activate
    elif [ -d "venv" ]; then
        echo "🔄 Activating Python virtual environment at ./venv"
        source venv/bin/activate
    else
        echo "⚠️  No Python virtual environment found. Please create one and install dependencies."
    fi
else
    echo "✅ Python virtual environment already activated: $VIRTUAL_ENV"
fi

echo "🚀 Starting AI Software Generator Platform"
echo "=========================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start infrastructure services
echo "🏗️  Starting infrastructure services..."
cd infra
docker-compose --env-file ../.env up -d
echo "✅ Infrastructure services started"

# Wait for services to be ready
echo "⏳ Waiting for infrastructure services to be ready..."
sleep 30

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
            return 1
        fi
        
        echo "⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
}

# Make startup scripts executable
chmod +x */start.sh

# Start all microservices in background
echo "🚀 Starting microservices..."

echo "Starting Auth Service..."
(cd auth-service && ./start.sh) &
AUTH_PID=$!

echo "Starting Orchestrator Service..."
(cd orchestrator && ./start.sh) &
ORCHESTRATOR_PID=$!

echo "Starting Codegen Service..."
(cd codegen-service && ./start.sh) &
CODEGEN_PID=$!

echo "Starting Executor Service..."
(cd executor-service && ./start.sh) &
EXECUTOR_PID=$!

echo "Starting Storage Service..."
(cd storage-service && ./start.sh) &
STORAGE_PID=$!

echo "Starting Audit Service..."
(cd audit-service && ./start.sh) &
AUDIT_PID=$!

echo "Starting API Gateway..."
(cd api-gateway && ./start.sh) &
GATEWAY_PID=$!

# Wait for services to start
sleep 10

echo "🔍 Checking service health..."

# Check each service
check_service "Auth Service" 8001
check_service "Orchestrator Service" 8002
check_service "Codegen Service" 8003
check_service "Executor Service" 8004
check_service "Storage Service" 8005
check_service "Audit Service" 8006
check_service "API Gateway" 8000

echo ""
echo "🎉 AI Software Generator Platform is ready!"
echo "=========================================="
echo ""
echo "📋 Service URLs:"
echo "  🌐 API Gateway:        http://localhost:8000"
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
echo "📖 API Documentation:   http://localhost:8000/docs"
echo "🩺 Health Check:        http://localhost:8000/health"
echo ""
echo "📝 Logs are available in: /Users/a.pothula/workspace/unity/AiTeam/logs/"
echo ""
echo "To stop all services: docker-compose -f infra/docker-compose.yml down"
echo "To view logs: tail -f /Users/a.pothula/workspace/unity/AiTeam/logs/*.log"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $AUTH_PID $ORCHESTRATOR_PID $CODEGEN_PID $EXECUTOR_PID $STORAGE_PID $AUDIT_PID $GATEWAY_PID 2>/dev/null || true
    cd infra && docker-compose down
    echo "✅ All services stopped"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Keep the script running
echo "Press Ctrl+C to stop all services"
wait
