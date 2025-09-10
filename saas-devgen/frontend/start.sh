#!/bin/bash

echo "🚀 Starting AI Software Generator Frontend Service..."
echo "=================================================="

cd "$(dirname "$0")"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Set environment variables
export NEXT_PUBLIC_API_GATEWAY_URL="http://localhost:8000"
export NEXT_PUBLIC_KEYCLOAK_URL="http://localhost:8080"

echo "🌐 Frontend Service Configuration:"
echo "   - API Gateway: $NEXT_PUBLIC_API_GATEWAY_URL"
echo "   - Keycloak: $NEXT_PUBLIC_KEYCLOAK_URL"
echo "   - Port: 3000"
echo ""

echo "✅ Starting Next.js development server..."
npm run dev
