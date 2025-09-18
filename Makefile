# Enterprise SaaS AI Software Generator - Makefile
# ================================================

.PHONY: help build test run clean logs

# Default target
help:
	@echo "Available commands:"
	@echo "  make build <service>    - Build a service Docker image"
	@echo "  make test <service>     - Run service tests"
	@echo "  make run <service>      - Start/restart a service"
	@echo ""
	@echo "Available services: gateway-service, profile-service, db, db-init"
	@echo ""
	@echo "Examples:"
	@echo "  make build profile-service"
	@echo "  make test gateway-service"
	@echo "  make run db"
	@echo "  make build db-init"
	@echo ""
	@echo "  make clean              - Clean up Docker images and containers"
	@echo "  make logs SERVICE=<name> - Show logs for a service"

# Build target with service argument
build:
	@if [ "$(word 2, $(MAKECMDGOALS))" = "gateway-service" ]; then \
		echo "🔨 Building gateway-service..."; \
		docker compose build gateway-service; \
	elif [ "$(word 2, $(MAKECMDGOALS))" = "profile-service" ]; then \
		echo "🔨 Building profile-service..."; \
		docker compose build profile-service; \
	elif [ "$(word 2, $(MAKECMDGOALS))" = "db" ]; then \
		echo "🔨 Building database..."; \
		docker compose build postgres; \
	elif [ "$(word 2, $(MAKECMDGOALS))" = "db-init" ]; then \
		echo "🔨 Building db-init..."; \
		docker compose build db-init; \
	else \
		echo "❌ Unknown service: $(word 2, $(MAKECMDGOALS))"; \
		echo "Available services: gateway-service, profile-service, db, db-init"; \
		exit 1; \
	fi

# Test target with service argument
test:
	@if [ "$(word 2, $(MAKECMDGOALS))" = "gateway-service" ]; then \
		echo "🧪 Testing gateway-service..."; \
		docker compose run --rm -e TEST_MODE=true gateway-service pytest; \
	elif [ "$(word 2, $(MAKECMDGOALS))" = "profile-service" ]; then \
		echo "🧪 Testing profile-service..."; \
		docker compose run --rm -e TEST_MODE=true profile-service pytest; \
	else \
		echo "❌ Unknown service: $(word 2, $(MAKECMDGOALS))"; \
		echo "Available services: gateway-service, profile-service"; \
		exit 1; \
	fi

# Run target with service argument
run:
	@if [ "$(word 2, $(MAKECMDGOALS))" = "gateway-service" ]; then \
		echo "🚀 Starting gateway-service..."; \
		docker compose up -d gateway-service; \
	elif [ "$(word 2, $(MAKECMDGOALS))" = "profile-service" ]; then \
		echo "🚀 Starting profile-service..."; \
		docker compose up -d profile-service; \
	elif [ "$(word 2, $(MAKECMDGOALS))" = "db" ]; then \
		echo "🚀 Starting database..."; \
		docker compose up -d postgres; \
	else \
		echo "❌ Unknown service: $(word 2, $(MAKECMDGOALS))"; \
		echo "Available services: gateway-service, profile-service, db"; \
		exit 1; \
	fi

# Utility Commands
clean:
	@echo "🧹 Cleaning up..."
	docker compose down --volumes --remove-orphans
	docker system prune -f

logs:
	@echo "📋 Showing logs for $(SERVICE)..."
	docker compose logs -f $(SERVICE)

# Dummy targets to prevent "No rule to make target" errors
%:
	@:
