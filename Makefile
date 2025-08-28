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

# PDF generation settings
PANDOC := pandoc
PDFS_DIR := pdfs
DOCS_DIR := docs
ROOT_MARKDOWN_FILES := README.md

# PDF generation functions
define install-pandoc
	@echo "$(YELLOW)Pandoc not found. Attempting installation...$(NC)"
	@OS_NAME="$$(uname -s)"; \
	case "$$OS_NAME" in \
		Linux*) \
			if command -v apt-get >/dev/null 2>&1; then \
				sudo apt-get update && sudo apt-get install -y pandoc; \
			else \
				echo "$(RED)apt-get not found. Please install Pandoc manually.$(NC)"; \
				echo "$(YELLOW)Visit: https://pandoc.org/installing.html$(NC)"; \
				exit 0; \
			fi ;; \
		Darwin*) \
			if command -v brew >/dev/null 2>&1; then \
				brew update && brew install pandoc; \
			else \
				echo "$(RED)Homebrew not found. Please install Pandoc manually.$(NC)"; \
				echo "$(YELLOW)Visit: https://pandoc.org/installing.html$(NC)"; \
				exit 0; \
			fi ;; \
		MINGW*|MSYS*|CYGWIN*) \
			if command -v winget >/dev/null 2>&1; then \
				winget install -e --id JohnMacFarlane.Pandoc --accept-package-agreements --accept-source-agreements; \
			else \
				echo "$(RED)winget not found. Please install Pandoc manually.$(NC)"; \
				echo "$(YELLOW)Visit: https://pandoc.org/installing.html$(NC)"; \
				exit 0; \
			fi ;; \
		*) \
			echo "$(RED)Unsupported OS for automatic Pandoc installation.$(NC)"; \
			echo "$(YELLOW)Visit: https://pandoc.org/installing.html$(NC)"; \
			exit 0 ;; \
	esac
endef

define install-pdf-engine
	@echo "$(YELLOW)No PDF engine found. Attempting to install MiKTeX for Windows...$(NC)"
	@OS_NAME="$$(uname -s)"; \
	if [ "$$OS_NAME" = "MINGW64_NT"* ] || [ "$$OS_NAME" = "MSYS_NT"* ] || [ "$$OS_NAME" = "CYGWIN_NT"* ]; then \
		if command -v winget >/dev/null 2>&1; then \
			echo "$(BLUE)Installing MiKTeX via winget...$(NC)"; \
			winget install -e --id MiKTeX.MiKTeX --accept-package-agreements --accept-source-agreements; \
			echo "$(GREEN)MiKTeX installation complete. Please restart your terminal and run make build again.$(NC)"; \
			exit 0; \
		else \
			echo "$(RED)winget not found. Please install MiKTeX manually.$(NC)"; \
			echo "$(YELLOW)Visit: https://miktex.org/download$(NC)"; \
			exit 0; \
		fi; \
	else \
		echo "$(YELLOW)Install with: $(shell if command -v brew >/dev/null 2>&1; then echo "brew install basictex"; elif command -v apt-get >/dev/null 2>&1; then echo "sudo apt-get install texlive-xetex"; elif command -v winget >/dev/null 2>&1; then echo "winget install -e --id MiKTeX.MiKTeX"; else echo "Visit https://www.tug.org/texlive/"; fi)$(NC)"; \
		exit 0; \
	fi
endef

define generate-pdfs
	@echo "$(GREEN)Generating PDFs from markdown files...$(NC)"
	@if ! command -v $(PANDOC) >/dev/null 2>&1; then \
		$(call install-pandoc) \
	fi
	@if command -v $(PANDOC) >/dev/null 2>&1; then \
		mkdir -p $(PDFS_DIR); \
		PDF_ENGINE=""; \
		if command -v xelatex >/dev/null 2>&1; then \
			PDF_ENGINE="--pdf-engine=xelatex"; \
		elif command -v pdflatex >/dev/null 2>&1; then \
			PDF_ENGINE="--pdf-engine=pdflatex"; \
		elif command -v wkhtmltopdf >/dev/null 2>&1; then \
			PDF_ENGINE="--pdf-engine=wkhtmltopdf"; \
		else \
			$(call install-pdf-engine) \
		fi; \
		for file in $(ROOT_MARKDOWN_FILES); do \
			if [ -f "$$file" ]; then \
				echo "$(BLUE)Converting $$file to PDF...$(NC)"; \
				$(PANDOC) "$$file" -o "$(PDFS_DIR)/$$(basename "$$file" .md).pdf" $$PDF_ENGINE --toc --number-sections; \
			fi; \
		done; \
		for file in $(DOCS_DIR)/*.md; do \
			if [ -f "$$file" ]; then \
				echo "$(BLUE)Converting $$file to PDF...$(NC)"; \
				$(PANDOC) "$$file" -o "$(PDFS_DIR)/$$(basename "$$file" .md).pdf" $$PDF_ENGINE --toc --number-sections; \
			fi; \
		done; \
		for file in $(DOCS_DIR)/api-groups/*.md; do \
			if [ -f "$$file" ]; then \
				echo "$(BLUE)Converting $$file to PDF...$(NC)"; \
				$(PANDOC) "$$file" -o "$(PDFS_DIR)/api-groups-$$(basename "$$file" .md).pdf" $$PDF_ENGINE --toc --number-sections; \
			fi; \
		done; \
		echo "$(GREEN)PDFs generated in $(PDFS_DIR)/$(NC)"; \
	else \
		echo "$(YELLOW)Pandoc installation failed - skipping PDF generation$(NC)"; \
	fi
endef

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
	@echo "  build       - Build the application and generate PDFs"
	@echo "  train       - Train ML models"
	@echo "  run         - Run the application"
	@echo "  clean       - Clean build artifacts"
	@echo "  verify      - Run tests, linting, formatting"
	@echo ""
	@echo "$(GREEN)Environments:$(NC)"
	@echo "  local       - Local development with uv"
	@echo "  docker      - Docker development"
	@echo "  remote      - Remote VM deployment (Vagrant)"
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make build           - Build with default environment (local)"
	@echo "  make build ENV=local - Build locally with uv"
	@echo "  make build local     - Build locally with uv (alternative syntax)"
	@echo "  make train docker    - Train with Docker"
	@echo "  make run remote      - Run in Vagrant VM"
	@echo "  make verify local    - Run all tests and checks locally"

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

verify:
	@echo "$(BLUE)Verifying for environment: $(ENV)$(NC)"
	@$(MAKE) verify-$(ENV)

verify-%:
	@echo "$(BLUE)Verifying for environment: $*$(NC)"
	@$(MAKE) verify-$*

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
	$(call generate-pdfs)
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
	@$(MAKE) ensure-redis
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

verify-local:
	@echo "$(GREEN)Running comprehensive verification locally...$(NC)"
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "$(RED)uv is not installed. Please install uv first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Running tests...$(NC)"
	@$(UV) run pytest test/ -v --cov=pollinexus
	@echo "$(GREEN)Running linting...$(NC)"
	@$(UV) run flake8 src/ test/
	@$(UV) run mypy src/
	@echo "$(GREEN)Running formatting check...$(NC)"
	@$(UV) run black --check src/ test/
	@$(UV) run isort --check-only src/ test/
	@echo "$(GREEN)Verification complete!$(NC)"

# Docker development targets
build-docker:
	@echo "$(GREEN)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache
	$(call generate-pdfs)
	@echo "$(GREEN)Docker build complete!$(NC)"

train-docker:
	@echo "$(GREEN)Training ML models with Docker...$(NC)"
	@$(DOCKER_COMPOSE) up --build --no-deps trainer
	@echo "$(GREEN)Docker training complete!$(NC)"

run-docker:
	@echo "$(GREEN)Running application with Docker...$(NC)"
	@$(DOCKER_COMPOSE) up --build
	@echo "$(GREEN)Docker application stopped.$(NC)"

verify-docker:
	@echo "$(GREEN)Running verification with Docker...$(NC)"
	@$(DOCKER_COMPOSE) run --rm app pytest test/ -v --cov=pollinexus
	@$(DOCKER_COMPOSE) run --rm app flake8 src/ test/
	@$(DOCKER_COMPOSE) run --rm app mypy src/
	@echo "$(GREEN)Docker verification complete!$(NC)"

# Remote deployment targets (Vagrant)
build-remote:
	@echo "$(GREEN)Building in remote VM...$(NC)"
	@$(MAKE) vagrant-up
	@echo "$(GREEN)Installing dependencies in VM...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && uv sync --dev"
	@echo "$(GREEN)Generating PDFs from markdown files...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && if ! command -v pandoc >/dev/null 2>&1; then echo 'Pandoc not found. Attempting installation...'; sudo apt-get update && sudo apt-get install -y pandoc; fi; if command -v pandoc >/dev/null 2>&1; then mkdir -p pdfs; PDF_ENGINE=''; if command -v xelatex >/dev/null 2>&1; then PDF_ENGINE='--pdf-engine=xelatex'; elif command -v pdflatex >/dev/null 2>&1; then PDF_ENGINE='--pdf-engine=pdflatex'; elif command -v wkhtmltopdf >/dev/null 2>&1; then PDF_ENGINE='--pdf-engine=wkhtmltopdf'; else echo 'No PDF engine found - attempting to install texlive-xetex...'; sudo apt-get update && sudo apt-get install -y texlive-xetex; fi; for file in README.md; do if [ -f \"\$$file\" ]; then echo 'Converting \$$file to PDF...'; pandoc \"\$$file\" -o \"pdfs/\$$(basename \"\$$file\" .md).pdf\" \$$PDF_ENGINE --toc --number-sections; fi; done; for file in docs/*.md; do if [ -f \"\$$file\" ]; then echo 'Converting \$$file to PDF...'; pandoc \"\$$file\" -o \"pdfs/\$$(basename \"\$$file\" .md).pdf\" \$$PDF_ENGINE --toc --number-sections; fi; done; for file in docs/api-groups/*.md; do if [ -f \"\$$file\" ]; then echo 'Converting \$$file to PDF...'; pandoc \"\$$file\" -o \"pdfs/api-groups-\$$(basename \"\$$file\" .md).pdf\" \$$PDF_ENGINE --toc --number-sections; fi; done; echo 'PDFs generated in pdfs/'; else echo 'Pandoc installation failed - skipping PDF generation'; fi"
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

verify-remote:
	@echo "$(GREEN)Running verification in remote VM...$(NC)"
	@$(MAKE) vagrant-up
	@$(VAGRANT) ssh -c "cd /vagrant && uv run pytest test/ -v --cov=pollinexus"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run flake8 src/ test/"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run mypy src/"
	@echo "$(GREEN)Remote verification complete!$(NC)"

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

ensure-redis:
	@echo "$(GREEN)Ensuring Redis is installed (local mode)...$(NC)"
	@if command -v redis-server >/dev/null 2>&1; then \
		echo "$(BLUE)redis-server found$(NC)"; \
	else \
		OS_NAME="$$(uname -s)"; \
		echo "$(YELLOW)redis-server not found. Attempting installation for $$OS_NAME...$(NC)"; \
		case "$$OS_NAME" in \
			Linux*) \
				if command -v apt-get >/dev/null 2>&1; then \
					sudo apt-get update && sudo apt-get install -y redis-server; \
				else \
					echo "$(RED)apt-get not found. Please install Redis manually.$(NC)"; \
					exit 1; \
				fi ;; \
			Darwin*) \
				if command -v brew >/dev/null 2>&1; then \
					brew update && brew install redis; \
				else \
					echo "$(RED)Homebrew not found. Please install Homebrew or Redis manually.$(NC)"; \
					exit 1; \
				fi ;; \
			MINGW*|MSYS*|CYGWIN*) \
				if command -v winget >/dev/null 2>&1; then \
					winget install -e --id Memurai.MemuraiDeveloper --accept-package-agreements --accept-source-agreements || true; \
					if ! command -v redis-server >/dev/null 2>&1; then \
						echo "$(YELLOW)Memurai installed as a Redis-compatible server. Ensure it is available in PATH or running as a service.$(NC)"; \
					fi; \
				else \
					echo "$(RED)winget not found. Please install Redis (or Memurai) manually.$(NC)"; \
					exit 1; \
				fi ;; \
			*) \
				echo "$(RED)Unsupported OS for automatic Redis installation.$(NC)"; \
				exit 1 ;; \
		esac; \
	fi
	@echo "$(GREEN)Redis check complete.$(NC)"

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
	@rm -rf .venv/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Clean complete!$(NC)"

clean-local:
	@echo "$(GREEN)Cleaning local artifacts...$(NC)"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Local clean complete!$(NC)"

clean-docker:
	@echo "$(GREEN)Cleaning Docker artifacts...$(NC)"
	@$(DOCKER_COMPOSE) down --volumes --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)Docker clean complete!$(NC)"

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

# Show current environment and tools
env-info:
	@echo "$(BLUE)Environment Information:$(NC)"
	@echo "$(BLUE)uv: $(shell if command -v $(UV) >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"
	@echo "$(BLUE)Docker: $(shell if command -v docker >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"
	@echo "$(BLUE)Docker Compose: $(shell if command -v docker-compose >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"
	@echo "$(BLUE)Vagrant: $(shell if command -v $(VAGRANT) >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"
	@echo "$(BLUE)VirtualBox: $(shell if command -v VBoxManage >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"
	@echo "$(BLUE)Pandoc: $(shell if command -v $(PANDOC) >/dev/null 2>&1; then echo "Available"; else echo "Not available"; fi)$(NC)"

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

setup-pandoc:
	@echo "$(GREEN)Setting up Pandoc for PDF generation...$(NC)"
	@if command -v $(PANDOC) >/dev/null 2>&1; then \
		echo "$(GREEN)Pandoc is already installed$(NC)"; \
	else \
		OS_NAME="$$(uname -s)"; \
		echo "$(YELLOW)Installing Pandoc for $$OS_NAME...$(NC)"; \
		case "$$OS_NAME" in \
			Linux*) \
				if command -v apt-get >/dev/null 2>&1; then \
					sudo apt-get update && sudo apt-get install -y pandoc texlive-xetex; \
				else \
					echo "$(RED)apt-get not found. Please install Pandoc manually.$(NC)"; \
					exit 1; \
				fi ;; \
			Darwin*) \
				if command -v brew >/dev/null 2>&1; then \
					brew update && brew install pandoc basictex; \
				else \
					echo "$(RED)Homebrew not found. Please install Homebrew or Pandoc manually.$(NC)"; \
					exit 1; \
				fi ;; \
			MINGW*|MSYS*|CYGWIN*) \
				if command -v winget >/dev/null 2>&1; then \
					winget install -e --id JohnMacFarlane.Pandoc --accept-package-agreements --accept-source-agreements; \
					winget install -e --id MiKTeX.MiKTeX --accept-package-agreements --accept-source-agreements; \
				else \
					echo "$(RED)winget not found. Please install Pandoc manually.$(NC)"; \
					exit 1; \
				fi ;; \
			*) \
				echo "$(RED)Unsupported OS for automatic Pandoc installation.$(NC)"; \
				exit 1 ;; \
		esac; \
	fi
	@echo "$(GREEN)Pandoc setup complete!$(NC)" 

# Setup local development environment
setup:
	@echo "$(BLUE)Setting up local development environment...$(NC)"
	@python -m pollinexus.cli setup

 

# KISS Principle Rules - DO NOT ADD NEW ARGUMENTS OR COMPLEX TARGETS
# 
# 1. Only use existing target patterns: build, train, run, clean, verify
# 2. Only use existing environments: local, docker, remote  
# 3. Never add new command-line arguments or parameters
# 4. Keep targets simple and focused on one task
# 5. Use existing infrastructure (uv, docker-compose, vagrant)
# 6. Auto-install dependencies within existing targets (like ensure-redis)
# 7. Maintain the pattern: make <target> <environment>
# 8. No new "dev", "prod", "setup" style targets - use existing ones 

