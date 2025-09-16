# Enterprise AI Software Generator Platform
# Production-ready Makefile for build and deployment

.PHONY: help build build-all run run-all stop clean test install deps check-deps setup-dev setup-prod docker-build docker-run k8s-deploy k8s-clean logs status status-all health backup restore setup-gateway-service setup-profile-service setup-codegen-service setup-executor-service setup-storage-service setup-audit-service setup-orchestrator setup-api-gateway build-gateway-service build-profile-service build-codegen-service build-executor-service build-storage-service build-audit-service build-orchestrator build-api-gateway run-gateway-service run-profile-service run-codegen-service run-executor-service run-storage-service run-audit-service run-orchestrator run-api-gateway stop-gateway-service stop-profile-service stop-codegen-service stop-executor-service stop-storage-service stop-audit-service stop-orchestrator stop-api-gateway

# Default target
help:
	@echo "Enterprise AI Software Generator Platform"
	@echo "========================================="
	@echo ""
	@echo "Available targets:"
	@echo "  help         Show this help message"
	@echo "  setup-dev    Setup development environment"
	@echo "  setup-prod   Setup production environment"
	@echo "  setup <name> Setup specific service (e.g., make setup db-init)"
	@echo "  install      Install all dependencies"
	@echo "  build        Build all services as Docker images"
	@echo "  build <name> Build specific service as Docker image (e.g., make build auth-service)"
	@echo "  run          Run all services in development mode"
	@echo "  run <name>   Run specific service (e.g., make run auth-service)"
	@echo "  run-bg       Run all services in background"
	@echo "  stop         Stop all running services"
	@echo "  stop <name>  Stop specific service (e.g., make stop auth-service)"
	@echo "  test         Run all tests from all services (alias for test-all)"
	@echo "  test-all     Run all tests from all services"
	@echo "  test <name>  Run specific service tests (e.g., make test auth-service)"
	@echo "  clean        Clean build artifacts and logs"
	@echo "  docker-build Build Docker images for all services"
	@echo "  docker-run   Start all services with Docker Compose"
	@echo "  docker-down  Stop all services"
	@echo "  docker-restart Restart all services"
	@echo "  docker-logs  Show logs for all services"
	@echo "  docker-status Show status of all services"
	@echo "  up-all       Start all services (alias)"
	@echo "  down-all     Stop all services (alias)"
	@echo "  restart-all  Restart all services (alias)"
	@echo "  logs-all     Show all logs (alias)"
	@echo "  status-all   Show all status (alias)"
	@echo "  k8s-deploy   Deploy to Kubernetes"
	@echo "  k8s-clean    Clean Kubernetes deployment"
	@echo "  logs         Show service logs"
	@echo "  status       Show service status (all services)"
	@echo "  status <name> Show specific service status (e.g., make status auth-service)"
	@echo "  health       Check health of all services"
	@echo "  backup       Backup database and storage"
	@echo "  restore      Restore from backup"

# Variables
DOCKER_COMPOSE_FILE = saas-devgen/infra/docker-compose.yml
SERVICES = gateway-service auth-service profile-service orchestrator codegen-service executor-service storage-service audit-service workflow-engine e2b-executor github-integration testing-framework advanced-metagpt
FRONTEND_DIR = saas-devgen/frontend

# Environment setup
setup-dev:
	@echo "Setting up development environment..."
	@python3 -m venv venv
	@./venv/bin/pip install --upgrade pip
	@make install
	@echo "Development environment ready!"

setup-prod:
	@echo "Setting up production environment..."
	@make check-deps
	@make install
	@make docker-build
	@echo "Production environment ready!"

# Dependency management
install:
	@echo "Installing dependencies for all services..."
	@for service in $(SERVICES); do \
		echo "Installing dependencies for $$service..."; \
		cd saas-devgen/$$service && pip install -r requirements.txt && cd ../..; \
	done
	@echo "All dependencies installed!"

check-deps:
	@echo "Checking system dependencies..."
	@command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
	@docker compose version >/dev/null 2>&1 || { echo "Docker Compose is required but not available. Aborting." >&2; exit 1; }
	@echo "All system dependencies are available!"

# Database setup targets are available as:
# make build db-init  - Build the db-init Docker service
# make run db-init    - Run database initialization with Flyway migrations

# Run targets
run-db-init:
	@echo "Starting DB Init Service (Docker)..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose up db-init; \
		if [ $$? -eq 0 ]; then \
			echo "✅ DB Init Service completed successfully!"; \
			echo "📊 Database schema initialized with Flyway migrations"; \
		else \
			echo "❌ Failed to run DB Init Service"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		exit 1; \
	fi

# Build targets (Docker images)
build-db-init:
	@echo "Building DB Init Service Docker image..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build db-init; \
		if [ $$? -eq 0 ]; then \
			echo "✅ DB Init Service Docker image built successfully!"; \
		else \
			echo "❌ Failed to build DB Init Service Docker image"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

# Handle multi-argument build command (e.g., make build auth-service)
build:
	@echo "Usage: make build <service-name>"
	@echo "Example: make build auth-service, make build codegen-service"
	@if [ -n "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		$(MAKE) build-$(filter-out $@,$(MAKECMDGOALS)); \
	else \
		$(MAKE) build-all; \
	fi

# Build all services (Docker images)
build-all:
	@echo "Building all Docker images..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build; \
		if [ $$? -eq 0 ]; then \
			echo "✅ All Docker images built successfully!"; \
		else \
			echo "❌ Failed to build Docker images"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

# Runtime targets
run-services:
	@echo "Starting application services..."
	@cd saas-devgen/auth-service && ./start.sh & echo $$! > auth.pid
	@sleep 2
	@cd saas-devgen/storage-service && ./start.sh & echo $$! > storage.pid
	@sleep 2
	@cd saas-devgen/audit-service && ./start.sh & echo $$! > audit.pid
	@sleep 2
	@cd saas-devgen/orchestrator && ./start.sh & echo $$! > orchestrator.pid
	@sleep 2
	@cd saas-devgen/codegen-service && ./start.sh & echo $$! > codegen.pid
	@sleep 2
	@cd saas-devgen/executor-service && ./start.sh & echo $$! > executor.pid
	@sleep 2
	@cd saas-devgen/workflow-engine && ./start.sh & echo $$! > workflow.pid
	@sleep 2
	@cd saas-devgen/e2b-executor && ./start.sh & echo $$! > e2b.pid
	@sleep 2
	@cd saas-devgen/github-integration && ./start.sh & echo $$! > github.pid
	@sleep 2
	@cd saas-devgen/testing-framework && ./start.sh & echo $$! > testing.pid
	@sleep 2
	@cd saas-devgen/advanced-metagpt && ./start.sh & echo $$! > metagpt.pid
	@sleep 3
	@cd saas-devgen/api-gateway && ./start.sh & echo $$! > gateway.pid
	@echo "All services started! Check status with 'make status'"

run-bg:
	@echo "Starting all services in background..."
	@make run > /dev/null 2>&1 &
	@echo "Services starting in background..."

# Handle multi-argument test command (e.g., make test auth-service)
test:
	@echo "Usage: make test <service-name>"
	@echo "Example: make test auth-service, make test codegen-service"
	@if [ -n "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		$(MAKE) test-$(filter-out $@,$(MAKECMDGOALS)); \
	else \
		$(MAKE) test-all; \
	fi

test-all:
	@echo "Running all tests from all services..."
	@make test-auth-service
	@make test-codegen-service
	@make test-executor-service
	@make test-storage-service
	@make test-audit-service
	@make test-orchestrator
	@make test-api-gateway
	@make test-gateway-service
	@echo "All service tests completed!"

# Handle multi-argument setup command (e.g., make setup auth-service)
setup:
	@echo "Usage: make setup <service-name>"
	@echo "Example: make setup db-init, make setup auth-service"
	@SERVICE_NAME="$(filter-out $@,$(MAKECMDGOALS))"; \
	if [ "$$SERVICE_NAME" = "db-init" ]; then \
		cd saas-devgen/db-init && pip install -r requirements.txt && echo "DB Init setup complete!"; \
	elif [ "$$SERVICE_NAME" = "auth-service" ]; then \
		cd saas-devgen/auth-service && pip install -r requirements.txt && echo "Auth Service setup complete!"; \
	elif [ "$$SERVICE_NAME" = "codegen-service" ]; then \
		cd saas-devgen/codegen-service && pip install -r requirements.txt && echo "Codegen Service setup complete!"; \
	elif [ "$$SERVICE_NAME" = "executor-service" ]; then \
		cd saas-devgen/executor-service && pip install -r requirements.txt && echo "Executor Service setup complete!"; \
	elif [ "$$SERVICE_NAME" = "storage-service" ]; then \
		cd saas-devgen/storage-service && pip install -r requirements.txt && echo "Storage Service setup complete!"; \
	elif [ "$$SERVICE_NAME" = "audit-service" ]; then \
		cd saas-devgen/audit-service && pip install -r requirements.txt && echo "Audit Service setup complete!"; \
	elif [ "$$SERVICE_NAME" = "orchestrator" ]; then \
		cd saas-devgen/orchestrator && pip install -r requirements.txt && echo "Orchestrator setup complete!"; \
	elif [ "$$SERVICE_NAME" = "api-gateway" ]; then \
		cd saas-devgen/api-gateway && pip install -r requirements.txt && echo "API Gateway setup complete!"; \
	elif [ "$$SERVICE_NAME" = "gateway-service" ]; then \
		echo "Gateway Service setup complete! (Kong-based)"; \
	else \
		echo "Error: Please specify a service name"; \
		echo "Available: db-init, auth-service, codegen-service, executor-service, storage-service, audit-service, orchestrator, api-gateway, gateway-service"; \
	fi

# Dummy target to consume extra arguments
%:
	@:

# Handle multi-argument run command (e.g., make run auth-service)
run:
	@echo "Usage: make run <service-name>"
	@echo "Example: make run auth-service"
	@if [ -n "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		$(MAKE) run-$(filter-out $@,$(MAKECMDGOALS)); \
	else \
		$(MAKE) run-services; \
	fi

# Handle multi-argument stop command (e.g., make stop auth-service)
stop:
	@echo "Usage: make stop <service-name>"
	@echo "Example: make stop auth-service"
	@if [ -n "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		$(MAKE) stop-$(filter-out $@,$(MAKECMDGOALS)); \
	else \
		$(MAKE) stop-all; \
	fi

# Generic test rule for individual services
test-%:
	@echo "Running $(*) Service tests..."
	@if [ -d "saas-devgen/$(*)/tests" ]; then \
		cd saas-devgen/$(*) && source ../../.venv/bin/activate && PYTHONPATH=../shared:../.. python -m pytest tests/ -v --tb=short; \
	else \
		echo "No tests found for $(*)"; \
	fi

# Specific service test rules (for backward compatibility)
test-auth-service:
	@echo "Running Auth Service tests..."
	@if [ -d "saas-devgen/auth-service/tests" ]; then \
		cd saas-devgen/auth-service && source ../../.venv/bin/activate && PYTHONPATH=../shared:../.. python -m pytest tests/ -v --tb=short; \
	else \
		echo "No tests found for auth-service"; \
	fi

test-codegen-service:
	@echo "Running Codegen Service tests..."
	@if [ -d "saas-devgen/codegen-service/tests" ]; then \
		cd saas-devgen/codegen-service && source ../../.venv/bin/activate && PYTHONPATH=../shared:../.. python -m pytest tests/ -v --tb=short; \
	else \
		echo "No tests found for codegen-service"; \
	fi

test-executor-service:
	@echo "Running Executor Service tests..."
	@if [ -d "saas-devgen/executor-service/tests" ]; then \
		cd saas-devgen/executor-service && source ../../.venv/bin/activate && PYTHONPATH=../shared:../.. python -m pytest tests/ -v --tb=short; \
	else \
		echo "No tests found for executor-service"; \
	fi

test-storage-service:
	@echo "Running Storage Service tests..."
	@if [ -d "saas-devgen/storage-service/tests" ]; then \
		cd saas-devgen/storage-service && source ../../.venv/bin/activate && PYTHONPATH=../shared:../.. python -m pytest tests/ -v --tb=short; \
	else \
		echo "No tests found for storage-service"; \
	fi

test-audit-service:
	@echo "Running Audit Service tests..."
	@if [ -d "saas-devgen/audit-service/tests" ]; then \
		cd saas-devgen/audit-service && source ../../.venv/bin/activate && PYTHONPATH=../shared:../.. python -m pytest tests/ -v --tb=short; \
	else \
		echo "No tests found for audit-service"; \
	fi

test-orchestrator:
	@echo "Running Orchestrator tests..."
	@if [ -d "saas-devgen/orchestrator/tests" ]; then \
		cd saas-devgen/orchestrator && source ../../.venv/bin/activate && PYTHONPATH=../shared:../.. python -m pytest tests/ -v --tb=short; \
	else \
		echo "No tests found for orchestrator"; \
	fi

test-api-gateway:
	@echo "Running API Gateway tests..."
	@if [ -d "saas-devgen/api-gateway/tests" ]; then \
		cd saas-devgen/api-gateway && source ../../.venv/bin/activate && PYTHONPATH=../shared:../.. python -m pytest tests/ -v --tb=short; \
	else \
		echo "No tests found for api-gateway"; \
	fi

test-gateway-service:
	@echo "Running Gateway Service tests..."
	@if [ -d "saas-devgen/gateway-service/tests" ]; then \
		cd saas-devgen/gateway-service && source ../../.venv/bin/activate && PYTHONPATH=../shared:../.. python -m pytest tests/ -v --tb=short; \
	else \
		echo "No tests found for gateway-service"; \
	fi

# Individual service management targets
# Setup targets
setup-auth-service:
	@echo "Setting up Auth Service..."
	@cd saas-devgen/auth-service && pip install -r requirements.txt
	@echo "Auth Service setup complete!"

setup-profile-service:
	@echo "Setting up Profile Service..."
	@cd saas-devgen/profile-service && pip install -r requirements.txt
	@echo "Profile Service setup complete!"

setup-codegen-service:
	@echo "Setting up Codegen Service..."
	@cd saas-devgen/codegen-service && pip install -r requirements.txt
	@echo "Codegen Service setup complete!"

setup-executor-service:
	@echo "Setting up Executor Service..."
	@cd saas-devgen/executor-service && pip install -r requirements.txt
	@echo "Executor Service setup complete!"

setup-storage-service:
	@echo "Setting up Storage Service..."
	@cd saas-devgen/storage-service && pip install -r requirements.txt
	@echo "Storage Service setup complete!"

setup-audit-service:
	@echo "Setting up Audit Service..."
	@cd saas-devgen/audit-service && pip install -r requirements.txt
	@echo "Audit Service setup complete!"

setup-orchestrator:
	@echo "Setting up Orchestrator..."
	@cd saas-devgen/orchestrator && pip install -r requirements.txt
	@echo "Orchestrator setup complete!"

setup-api-gateway:
	@echo "Setting up API Gateway..."
	@cd saas-devgen/api-gateway && pip install -r requirements.txt
	@echo "API Gateway setup complete!"

# Build targets (Docker images)
build-auth-service:
	@echo "Building Auth Service Docker image..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build auth-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Auth Service Docker image built successfully!"; \
		else \
			echo "❌ Failed to build Auth Service Docker image"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

build-profile-service:
	@echo "Building Profile Service Docker image..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build profile-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Profile Service Docker image built successfully!"; \
		else \
			echo "❌ Failed to build Profile Service Docker image"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

build-codegen-service:
	@echo "Building Codegen Service Docker image..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build codegen-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Codegen Service Docker image built successfully!"; \
		else \
			echo "❌ Failed to build Codegen Service Docker image"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

build-executor-service:
	@echo "Building Executor Service Docker image..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build executor-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Executor Service Docker image built successfully!"; \
		else \
			echo "❌ Failed to build Executor Service Docker image"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

build-storage-service:
	@echo "Building Storage Service Docker image..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build storage-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Storage Service Docker image built successfully!"; \
		else \
			echo "❌ Failed to build Storage Service Docker image"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

build-audit-service:
	@echo "Building Audit Service Docker image..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build audit-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Audit Service Docker image built successfully!"; \
		else \
			echo "❌ Failed to build Audit Service Docker image"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

build-orchestrator:
	@echo "Building Orchestrator Docker image..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build orchestrator; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Orchestrator Docker image built successfully!"; \
		else \
			echo "❌ Failed to build Orchestrator Docker image"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

build-api-gateway:
	@echo "Building API Gateway Docker image..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build api-gateway; \
		if [ $$? -eq 0 ]; then \
			echo "✅ API Gateway Docker image built successfully!"; \
		else \
			echo "❌ Failed to build API Gateway Docker image"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

build-gateway-service:
	@echo "Building Gateway Service (Kong-based)..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose build gateway-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Gateway Service (Kong) built successfully!"; \
		else \
			echo "❌ Failed to build Gateway Service"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		echo "Please install Docker and Docker Compose to build services"; \
		exit 1; \
	fi

# Run targets
run-auth-service:
	@echo "Starting Auth Service (Docker)..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose up -d auth-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Auth Service started successfully!"; \
			echo "🌐 Service URL: http://localhost:${AUTH_SERVICE_PORT:-8004}"; \
			echo "📖 API Docs: http://localhost:${AUTH_SERVICE_PORT:-8004}/docs"; \
			echo "🔄 Health: http://localhost:${AUTH_SERVICE_PORT:-8004}/health"; \
		else \
			echo "❌ Failed to start Auth Service"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		exit 1; \
	fi

run-profile-service:
	@echo "Starting Profile Service (Docker)..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		export PROFILE_SERVICE_PORT=$$(grep '^PROFILE_SERVICE_PORT=' .env | cut -d'=' -f2 || echo '8005'); \
		docker compose up -d profile-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Profile Service started successfully!"; \
			echo "🌐 Service URL: http://localhost:$${PROFILE_SERVICE_PORT}"; \
			echo "📖 API Docs: http://localhost:$${PROFILE_SERVICE_PORT}/docs"; \
			echo "🔄 Health: http://localhost:$${PROFILE_SERVICE_PORT}/health"; \
		else \
			echo "❌ Failed to start Profile Service"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		exit 1; \
	fi

run-codegen-service:
	@echo "Starting Codegen Service..."
	@cd saas-devgen/codegen-service && ./start.sh & echo $$! > codegen.pid
	@echo "Codegen Service started! PID: $$(cat codegen.pid)"

run-executor-service:
	@echo "Starting Executor Service..."
	@cd saas-devgen/executor-service && ./start.sh & echo $$! > executor.pid
	@echo "Executor Service started! PID: $$(cat executor.pid)"

run-storage-service:
	@echo "Starting Storage Service..."
	@cd saas-devgen/storage-service && ./start.sh & echo $$! > storage.pid
	@echo "Storage Service started! PID: $$(cat storage.pid)"

run-audit-service:
	@echo "Starting Audit Service..."
	@cd saas-devgen/audit-service && ./start.sh & echo $$! > audit.pid
	@echo "Audit Service started! PID: $$(cat audit.pid)"

run-orchestrator:
	@echo "Starting Orchestrator..."
	@cd saas-devgen/orchestrator && ./start.sh & echo $$! > orchestrator.pid
	@echo "Orchestrator started! PID: $$(cat orchestrator.pid)"

run-api-gateway:
	@echo "Starting API Gateway..."
	@cd saas-devgen/api-gateway && ./start.sh & echo $$! > gateway.pid
	@echo "API Gateway started! PID: $$(cat gateway.pid)"

run-gateway-service:
	@echo "Starting Gateway Service (Kong)..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose up -d gateway-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Gateway Service (Kong) started successfully!"; \
			echo "Kong Proxy: http://localhost:8000"; \
			echo "Kong Admin API: http://localhost:8001"; \
			echo "Kong Admin GUI: http://localhost:8002"; \
		else \
			echo "❌ Failed to start Gateway Service"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		exit 1; \
	fi

# Stop targets
stop-auth-service:
	@echo "Stopping Auth Service (Docker)..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose down auth-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Auth Service stopped successfully!"; \
		else \
			echo "❌ Failed to stop Auth Service"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		exit 1; \
	fi

stop-profile-service:
	@echo "Stopping Profile Service (Docker)..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose down profile-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Profile Service stopped successfully!"; \
		else \
			echo "❌ Failed to stop Profile Service"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		exit 1; \
	fi

stop-codegen-service:
	@echo "Stopping Codegen Service..."
	@-if [ -f "saas-devgen/codegen-service/codegen.pid" ]; then \
		kill `cat saas-devgen/codegen-service/codegen.pid` 2>/dev/null || true; \
		rm -f saas-devgen/codegen-service/codegen.pid; \
	fi
	@echo "Codegen Service stopped!"

stop-executor-service:
	@echo "Stopping Executor Service..."
	@-if [ -f "saas-devgen/executor-service/executor.pid" ]; then \
		kill `cat saas-devgen/executor-service/executor.pid` 2>/dev/null || true; \
		rm -f saas-devgen/executor-service/executor.pid; \
	fi
	@echo "Executor Service stopped!"

stop-storage-service:
	@echo "Stopping Storage Service..."
	@-if [ -f "saas-devgen/storage-service/storage.pid" ]; then \
		kill `cat saas-devgen/storage-service/storage.pid` 2>/dev/null || true; \
		rm -f saas-devgen/storage-service/storage.pid; \
	fi
	@echo "Storage Service stopped!"

stop-audit-service:
	@echo "Stopping Audit Service..."
	@-if [ -f "saas-devgen/audit-service/audit.pid" ]; then \
		kill `cat saas-devgen/audit-service/audit.pid` 2>/dev/null || true; \
		rm -f saas-devgen/audit-service/audit.pid; \
	fi
	@echo "Audit Service stopped!"

stop-orchestrator:
	@echo "Stopping Orchestrator..."
	@-if [ -f "saas-devgen/orchestrator/orchestrator.pid" ]; then \
		kill `cat saas-devgen/orchestrator/orchestrator.pid` 2>/dev/null || true; \
		rm -f saas-devgen/orchestrator/orchestrator.pid; \
	fi
	@echo "Orchestrator stopped!"

stop-api-gateway:
	@echo "Stopping API Gateway..."
	@-if [ -f "saas-devgen/api-gateway/gateway.pid" ]; then \
		kill `cat saas-devgen/api-gateway/gateway.pid` 2>/dev/null || true; \
		rm -f saas-devgen/api-gateway/gateway.pid; \
	fi
	@echo "API Gateway stopped!"

stop-gateway-service:
	@echo "Stopping Gateway Service (Kong)..."
	@if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then \
		docker compose down gateway-service; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Gateway Service (Kong) stopped successfully!"; \
		else \
			echo "❌ Failed to stop Gateway Service"; \
			exit 1; \
		fi \
	else \
		echo "❌ Docker or Docker Compose not available"; \
		exit 1; \
	fi

# Cleanup
clean:
	@echo "Cleaning build artifacts and logs..."
	@make clean-logs
	@make clean-cache
	@make clean-temp
	@echo "Cleanup complete!"

clean-logs:
	@echo "Cleaning log files..."
	@rm -f logs/*.log
	@rm -f saas-devgen/*/*.log
	@find . -name "*.log" -delete

clean-cache:
	@echo "Cleaning Python cache..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete

clean-temp:
	@echo "Cleaning temporary files..."
	@rm -rf /tmp/ai-devgen-*
	@rm -f saas-devgen/*/*.pid

# Docker operations
docker-build: ## Build all Docker images
	@echo "Building all Docker images..."
	docker compose build

docker-run: ## Start all services with Docker Compose
	@echo "Starting all enterprise services..."
	docker compose up -d

docker-down: ## Stop all services
	@echo "Stopping all enterprise services..."
	docker compose down

docker-restart: docker-down docker-run ## Restart all services

docker-logs: ## Show logs for all services
	@echo "Showing logs for all services..."
	docker compose logs -f

docker-status: ## Show status of all services
	@echo "Checking Docker Compose services status..."
	docker compose ps

up-all: docker-run ## Start all services (alias for docker-run)

down-all: docker-down ## Stop all services (alias for docker-down)

restart-all: docker-restart ## Restart all services (alias for docker-restart)

logs-all: docker-logs ## Show all logs (alias for docker-logs)

status-all: docker-status ## Show all status (alias for docker-status)

# Kubernetes operations
k8s-deploy:
	@echo "Deploying to Kubernetes..."
	@kubectl apply -f saas-devgen/k8s/infrastructure.yaml
	@kubectl apply -f saas-devgen/k8s/security.yaml
	@kubectl apply -f saas-devgen/k8s/services.yaml
	@kubectl apply -f saas-devgen/k8s/ai-services.yaml
	@echo "Deployment to Kubernetes complete!"

k8s-clean:
	@echo "Cleaning Kubernetes deployment..."
	@kubectl delete -f saas-devgen/k8s/ai-services.yaml --ignore-not-found=true
	@kubectl delete -f saas-devgen/k8s/services.yaml --ignore-not-found=true
	@kubectl delete -f saas-devgen/k8s/security.yaml --ignore-not-found=true
	@kubectl delete -f saas-devgen/k8s/infrastructure.yaml --ignore-not-found=true
	@echo "Kubernetes cleanup complete!"

# Monitoring and status
logs:
	@echo "Showing recent logs from all services..."
	@echo "=== API Gateway ==="
	@tail -n 20 logs/api-gateway.log 2>/dev/null || echo "No logs found"
	@echo "=== Auth Service ==="
	@tail -n 20 logs/auth-service.log 2>/dev/null || echo "No logs found"
	@echo "=== Orchestrator ==="
	@tail -n 20 logs/orchestrator.log 2>/dev/null || echo "No logs found"
	@echo "=== Codegen Service ==="
	@tail -n 20 logs/codegen-service.log 2>/dev/null || echo "No logs found"

# Handle multi-argument status command (e.g., make status auth-service)
status:
	@echo "Usage: make status [service-name]"
	@echo "Example: make status, make status auth-service"
	@if [ -n "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		SERVICE_NAME="$(filter-out $@,$(MAKECMDGOALS))"; \
		echo "Checking $$SERVICE_NAME status..."; \
		case $$SERVICE_NAME in \
			"auth-service") \
				ps aux | grep -E "(uvicorn.*auth-service|auth-service.*uvicorn)" | grep -v grep | head -5 || echo "$$SERVICE_NAME is not running" ;; \
			"codegen-service") \
				ps aux | grep -E "(uvicorn.*codegen-service|codegen-service.*uvicorn)" | grep -v grep | head -5 || echo "$$SERVICE_NAME is not running" ;; \
			"executor-service") \
				ps aux | grep -E "(uvicorn.*executor-service|executor-service.*uvicorn)" | grep -v grep | head -5 || echo "$$SERVICE_NAME is not running" ;; \
			"storage-service") \
				ps aux | grep -E "(uvicorn.*storage-service|storage-service.*uvicorn)" | grep -v grep | head -5 || echo "$$SERVICE_NAME is not running" ;; \
			"audit-service") \
				ps aux | grep -E "(uvicorn.*audit-service|audit-service.*uvicorn)" | grep -v grep | head -5 || echo "$$SERVICE_NAME is not running" ;; \
			"orchestrator") \
				ps aux | grep -E "(uvicorn.*orchestrator|orchestrator.*uvicorn)" | grep -v grep | head -5 || echo "$$SERVICE_NAME is not running" ;; \
			"api-gateway") \
				ps aux | grep -E "(uvicorn.*api-gateway|api-gateway.*uvicorn)" | grep -v grep | head -5 || echo "$$SERVICE_NAME is not running" ;; \
			*) \
				echo "Unknown service: $$SERVICE_NAME"; \
				echo "Available: auth-service, codegen-service, executor-service, storage-service, audit-service, orchestrator, api-gateway" ;; \
		esac \
	else \
		$(MAKE) status-all; \
	fi

# Show status of all services
status-all:
	@echo "Checking service status..."
	@echo "Service Status Report"
	@echo "===================="
	@ps aux | grep -E "(uvicorn|main:app)" | grep -v grep | awk '{print $$NF}' | sort || echo "No services running"

health:
	@echo "Checking health of all services..."
	@make test-api

# Backup and restore
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	@cd saas-devgen/infra && docker compose exec postgres pg_dump -U devgen devgen > ../../backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backup created!"

restore:
	@echo "Restoring from backup..."
	@echo "Please specify backup file: make restore BACKUP_FILE=backups/db_backup_YYYYMMDD_HHMMSS.sql"
	@if [ -n "$(BACKUP_FILE)" ]; then \
		cd saas-devgen/infra && docker compose exec -T postgres psql -U devgen -d devgen < ../../$(BACKUP_FILE); \
		echo "Database restored from $(BACKUP_FILE)!"; \
	fi

# Development helpers
dev-setup: setup-dev run status
	@echo "Development environment is ready!"
	@echo "Access the API at: http://localhost:8000"
	@echo "Use 'make logs' to view logs"
	@echo "Use 'make stop' to stop all services"

prod-setup: setup-prod docker-build docker-run
	@echo "Production environment is ready!"
	@echo "Services are running in Docker containers"

# Quality checks
lint:
	@echo "Running code quality checks..."
	@for service in $(SERVICES); do \
		echo "Linting $$service..."; \
		cd saas-devgen/$$service && python -m flake8 main.py --max-line-length=120 2>/dev/null || echo "Linting not available for $$service"; \
		cd ../..; \
	done

security-scan:
	@echo "Running security scans..."
	@for service in $(SERVICES); do \
		echo "Scanning $$service..."; \
		cd saas-devgen/$$service && python -m bandit main.py -f json 2>/dev/null || echo "Security scan not available for $$service"; \
		cd ../..; \
	done

# Documentation
docs:
	@echo "Generating documentation..."
	@mkdir -p docs/api
	@echo "API documentation will be available at service endpoints /docs"
	@echo "Example: http://localhost:8000/docs"

# Full system reset
reset: stop clean db-reset start
	@echo "🔄 Full system reset complete"
