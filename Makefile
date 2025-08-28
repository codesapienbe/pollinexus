# Pollinexus Makefile - Development and Deployment Automation
# Usage: make <target> <environment>
# Examples: make build local, make train docker, make run remote

# Default environment
ENV ?= local

# Python and application settings
APP_NAME := pollinexus
VENV := .venv
PYTHON_VENV := $(VENV)/bin/python
UV := uv

# Docker settings
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_PROD := docker-compose -f docker-compose.prod.yml

# Development server settings
DEV_HOST := 0.0.0.0
DEV_PORT := 8000
DEV_WORKERS := 1
DEV_RELOAD := true

# Production server settings
PROD_HOST := 0.0.0.0
PROD_PORT := 8000
PROD_WORKERS := 4

# Celery settings
CELERY_WORKERS := 2
CELERY_BEAT := true

# Database settings
DB_URL := duckdb:///pollinexus.db

# Vagrant settings
VAGRANT := vagrant
VAGRANT_BOX := ubuntu/focal64
VAGRANT_VM_NAME := pollinexus-dev

# Colors for output (disable if not a TTY)
ifeq ($(shell test -t 1 && echo tty || echo notty),tty)
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color
else
GREEN :=
YELLOW :=
RED :=
BLUE :=
NC :=
endif

.PHONY: help build train run clean install test lint format local docker remote

# Default target
help:
	@echo "$(BLUE)Pollinexus Development and Deployment Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Command Format:$(NC)"
	@echo "  make <target> <environment>"
	@echo ""
	@echo "$(GREEN)Targets:$(NC)"
	@echo "  build       - Build the application"
	@echo "  train       - Train ML models"
	@echo "  run         - Run the application"
	@echo "  dev         - Run in development mode"
	@echo "  prod        - Run in production mode"
	@echo ""
	@echo "$(GREEN)Environments:$(NC)"
	@echo "  local       - Local development with uv"
	@echo "  docker      - Docker development"
	@echo "  remote      - Remote VM deployment (Vagrant)"
	@echo ""
	@echo "$(GREEN)Utility Targets:$(NC)"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean build artifacts"
	@echo "  vagrant-up  - Start Vagrant VM"
	@echo "  vagrant-down - Stop Vagrant VM"
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make build           - Build with default environment (local)"
	@echo "  make build ENV=local - Build locally with uv"
	@echo "  make build local     - Build locally with uv (alternative syntax)"
	@echo "  make train docker    - Train with Docker"
	@echo "  make run remote      - Run in Vagrant VM"
	@echo "  make dev local       - Local development"
	@echo "  make prod docker     - Docker production"

# Main targets with environment routing
build:
	@echo "$(BLUE)Building for environment: $(ENV)$(NC)"
	@$(MAKE) build-$(ENV)

build-%:
	@echo "$(BLUE)Building for environment: $*$(NC)"
	@$(MAKE) build-$*

train:
	@echo "$(BLUE)Training for environment: $(ENV)$(NC)"
	@$(MAKE) train-$(ENV)

train-%:
	@echo "$(BLUE)Training for environment: $*$(NC)"
	@$(MAKE) train-$*

run:
	@echo "$(BLUE)Running for environment: $(ENV)$(NC)"
	@$(MAKE) run-$(ENV)

run-%:
	@echo "$(BLUE)Running for environment: $*$(NC)"
	@$(MAKE) run-$*

# Local development targets (using uv)
build-local:
	@echo "$(GREEN)Building locally with uv...$(NC)"
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "$(RED)uv is not installed. Please install uv first.$(NC)"; \
		echo "$(YELLOW)Install with: curl -LsSf https://astral.sh/uv/install.sh | sh$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Installing dependencies with uv...$(NC)"
	@$(UV) sync --dev
	@echo "$(GREEN)Local build complete!$(NC)"

train-local:
	@echo "$(GREEN)Training ML models locally...$(NC)"
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "$(RED)uv is not installed. Please install uv first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Running training pipeline...$(NC)"
	@$(UV) run python -m pollinexus.cli train-models
	@echo "$(GREEN)Training complete!$(NC)"

run-local:
	@echo "$(GREEN)Running application locally...$(NC)"
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "$(RED)uv is not installed. Please install uv first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Starting FastAPI server...$(NC)"
	@POLLINEXUS_DISABLE_SECURITY_FOR_LOCAL=true $(UV) run uvicorn pollinexus.api.main:app \
		--host $(DEV_HOST) \
		--port $(DEV_PORT) \
		$(if $(filter true,$(DEV_RELOAD)),--reload) \
		--workers $(DEV_WORKERS) & \
		echo "$(GREEN)Starting Jupyter Lab for notebooks...$(NC)"; \
		$(UV) run jupyter lab --no-browser --NotebookApp.token='' --NotebookApp.password='' --ip=$(DEV_HOST) --port=8888 --notebook-dir=src/pollinexus/notebook
	@echo "$(GREEN)Application running at http://$(DEV_HOST):$(DEV_PORT)$(NC)"
	@echo "$(GREEN)Jupyter Lab running at http://$(DEV_HOST):8888$(NC)"
	

dev-local:
	@echo "$(GREEN)Starting development server locally...$(NC)"
	@$(MAKE) build-local
	@echo "$(GREEN)Starting development server with auto-reload...$(NC)"
	@$(UV) run uvicorn pollinexus.api.main:app \
		--host $(DEV_HOST) \
		--port $(DEV_PORT) \
		--reload \
		--workers 1

prod-local:
	@echo "$(GREEN)Starting production server locally...$(NC)"
	@$(MAKE) build-local
	@echo "$(GREEN)Starting production server with Gunicorn...$(NC)"
	@$(UV) run gunicorn pollinexus.api.main:app \
		--bind $(PROD_HOST):$(PROD_PORT) \
		--workers $(PROD_WORKERS) \
		--worker-class uvicorn.workers.UvicornWorker \
		--timeout 30 \
		--keep-alive 5

# Docker development targets
build-docker:
	@echo "$(GREEN)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache
	@echo "$(GREEN)Docker build complete!$(NC)"

train-docker:
	@echo "$(GREEN)Training ML models with Docker...$(NC)"
	@$(DOCKER_COMPOSE) up --build --no-deps trainer
	@echo "$(GREEN)Docker training complete!$(NC)"

run-docker:
	@echo "$(GREEN)Running application with Docker...$(NC)"
	@$(DOCKER_COMPOSE) up --build
	@echo "$(GREEN)Docker application stopped.$(NC)"

dev-docker:
	@echo "$(GREEN)Starting development environment with Docker...$(NC)"
	@$(DOCKER_COMPOSE) up --build -d
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "$(BLUE)API available at: http://localhost:$(DEV_PORT)$(NC)"
	@echo "$(BLUE)Docs available at: http://localhost:$(DEV_PORT)/docs$(NC)"
	@echo "$(YELLOW)Use 'make logs-docker' to view logs$(NC)"

prod-docker:
	@echo "$(GREEN)Starting production environment with Docker...$(NC)"
	@$(DOCKER_COMPOSE_PROD) up --build -d
	@echo "$(GREEN)Production environment started!$(NC)"
	@echo "$(BLUE)API available at: http://localhost:$(PROD_PORT)$(NC)"
	@echo "$(YELLOW)Use 'make logs-docker' to view logs$(NC)"

# Remote deployment targets (Vagrant)
build-remote:
	@echo "$(GREEN)Building in remote VM...$(NC)"
	@$(MAKE) vagrant-up
	@echo "$(GREEN)Installing dependencies in VM...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && uv sync --dev"
	@echo "$(GREEN)Remote build complete!$(NC)"

train-remote:
	@echo "$(GREEN)Training ML models in remote VM...$(NC)"
	@$(MAKE) vagrant-up
	@echo "$(GREEN)Running training pipeline in VM...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run python -m pollinexus.cli train-models"
	@echo "$(GREEN)Remote training complete!$(NC)"

run-remote:
	@echo "$(GREEN)Running application in remote VM...$(NC)"
	@$(MAKE) vagrant-up
	@echo "$(GREEN)Starting FastAPI server in VM...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run uvicorn pollinexus.api.main:app --host 0.0.0.0 --port $(DEV_PORT) --reload"

dev-remote:
	@echo "$(GREEN)Starting development server in remote VM...$(NC)"
	@$(MAKE) build-remote
	@echo "$(GREEN)Starting development server with auto-reload in VM...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run uvicorn pollinexus.api.main:app --host 0.0.0.0 --port $(DEV_PORT) --reload --workers 1"

prod-remote:
	@echo "$(GREEN)Starting production server in remote VM...$(NC)"
	@$(MAKE) build-remote
	@echo "$(GREEN)Starting production server with Gunicorn in VM...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run gunicorn pollinexus.api.main:app --bind 0.0.0.0:$(PROD_PORT) --workers $(PROD_WORKERS) --worker-class uvicorn.workers.UvicornWorker --timeout 30 --keep-alive 5"

# Vagrant management
vagrant-up:
	@echo "$(GREEN)Starting Vagrant VM...$(NC)"
	@if ! command -v $(VAGRANT) >/dev/null 2>&1; then \
		echo "$(RED)Vagrant is not installed. Please install Vagrant first.$(NC)"; \
		exit 1; \
	fi
	@$(VAGRANT) up
	@echo "$(GREEN)Vagrant VM is ready!$(NC)"
	@echo "$(BLUE)SSH into VM: vagrant ssh$(NC)"
	@echo "$(BLUE)API will be available at: http://localhost:$(DEV_PORT)$(NC)"

vagrant-down:
	@echo "$(GREEN)Stopping Vagrant VM...$(NC)"
	@$(VAGRANT) halt

vagrant-destroy:
	@echo "$(RED)Destroying Vagrant VM...$(NC)"
	@$(VAGRANT) destroy -f

vagrant-ssh:
	@echo "$(GREEN)SSH into Vagrant VM...$(NC)"
	@$(VAGRANT) ssh

vagrant-status:
	@echo "$(GREEN)Vagrant VM status...$(NC)"
	@$(VAGRANT) status

# Utility targets
install:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) sync --dev; \
	else \
		$(PIP) install -e ".[dev]"; \
	fi
	@echo "$(GREEN)Dependencies installed!$(NC)"

test:
	@echo "$(GREEN)Running tests...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run pytest test/ -v --cov=pollinexus; \
	else \
		$(PYTHON) -m pytest test/ -v --cov=pollinexus; \
	fi

lint:
	@echo "$(GREEN)Running linting...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run flake8 src/ test/; \
		$(UV) run mypy src/; \
	else \
		$(PYTHON) -m flake8 src/ test/; \
		$(PYTHON) -m mypy src/; \
	fi

format:
	@echo "$(GREEN)Formatting code...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run black src/ test/; \
		$(UV) run isort src/ test/; \
	else \
		$(PYTHON) -m black src/ test/; \
		$(PYTHON) -m isort src/ test/; \
	fi

clean:
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -delete
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Clean complete!$(NC)"

# Docker utility targets
logs-docker:
	@echo "$(GREEN)Showing Docker logs...$(NC)"
	@$(DOCKER_COMPOSE) logs -f

stop-docker:
	@echo "$(GREEN)Stopping Docker services...$(NC)"
	@$(DOCKER_COMPOSE) down

restart-docker:
	@echo "$(GREEN)Restarting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) restart

# Database targets
db-init:
	@echo "$(GREEN)Initializing database...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run python -m pollinexus.cli init-db; \
	else \
		$(PYTHON) -m pollinexus.cli init-db; \
	fi

db-migrate:
	@echo "$(GREEN)Running database migrations...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run alembic upgrade head; \
	else \
		$(PYTHON) -m alembic upgrade head; \
	fi

# Celery targets
celery-worker:
	@echo "$(GREEN)Starting Celery worker...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run celery -A pollinexus.tasks.celery_app worker --loglevel=info; \
	else \
		$(PYTHON) -m celery -A pollinexus.tasks.celery_app worker --loglevel=info; \
	fi

celery-beat:
	@echo "$(GREEN)Starting Celery beat scheduler...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run celery -A pollinexus.tasks.celery_app beat --loglevel=info; \
	else \
		$(PYTHON) -m celery -A pollinexus.tasks.celery_app beat --loglevel=info; \
	fi

# Health check targets
health:
	@echo "$(GREEN)Checking application health...$(NC)"
	@curl -f http://localhost:$(DEV_PORT)/health || echo "$(RED)Health check failed$(NC)"

health-detailed:
	@echo "$(GREEN)Checking detailed application health...$(NC)"
	@curl -f http://localhost:$(DEV_PORT)/health/detailed || echo "$(RED)Detailed health check failed$(NC)"

# Quick start targets
quick-start-local:
	@echo "$(GREEN)Quick start - Local development with uv...$(NC)"
	@$(MAKE) dev-local

quick-start-docker:
	@echo "$(GREEN)Quick start - Docker development...$(NC)"
	@$(MAKE) dev-docker

quick-start-remote:
	@echo "$(GREEN)Quick start - Remote VM development...$(NC)"
	@$(MAKE) dev-remote

# Show current environment and tools
env-info:
	@echo "$(BLUE)Environment Information:$(NC)"
	@echo "$(BLUE)uv: $(shell if command -v $(UV) >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"
	@echo "$(BLUE)Docker: $(shell if command -v docker >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"
	@echo "$(BLUE)Docker Compose: $(shell if command -v docker-compose >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"
	@echo "$(BLUE)Vagrant: $(shell if command -v $(VAGRANT) >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"
	@echo "$(BLUE)VirtualBox: $(shell if command -v VBoxManage >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"

# Setup targets for first-time users
setup-local:
	@echo "$(GREEN)Setting up local development environment...$(NC)"
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "$(YELLOW)Installing uv...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)Please restart your terminal or run: source ~/.bashrc$(NC)"; \
	else \
		echo "$(GREEN)uv is already installed$(NC)"; \
	fi

setup-docker:
	@echo "$(GREEN)Setting up Docker environment...$(NC)"
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "$(RED)Docker is not installed. Please install Docker first.$(NC)"; \
		exit 1; \
	fi
	@if ! command -v docker-compose >/dev/null 2>&1; then \
		echo "$(RED)Docker Compose is not installed. Please install Docker Compose first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Docker environment is ready!$(NC)"

setup-remote:
	@echo "$(GREEN)Setting up remote development environment...$(NC)"
	@if ! command -v $(VAGRANT) >/dev/null 2>&1; then \
		echo "$(RED)Vagrant is not installed. Please install Vagrant first.$(NC)"; \
		exit 1; \
	fi
	@if ! command -v VBoxManage >/dev/null 2>&1; then \
		echo "$(RED)VirtualBox is not installed. Please install VirtualBox first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Remote environment is ready!$(NC)" 