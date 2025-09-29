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

# Utility functions
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
	@mkdir -p $(PDFS_DIR) || true
	@OS_NAME="$$(uname -s)"; \
	if command -v $(PANDOC) >/dev/null 2>&1; then \
		echo "$(BLUE)Pandoc found, checking for PDF engines on $$OS_NAME...$(NC)"; \
		PDF_ENGINE=""; \
		if command -v xelatex >/dev/null 2>&1; then \
			PDF_ENGINE="--pdf-engine=xelatex"; \
			echo "$(BLUE)Using xelatex engine$(NC)"; \
		elif command -v pdflatex >/dev/null 2>&1; then \
			PDF_ENGINE="--pdf-engine=pdflatex"; \
			echo "$(BLUE)Using pdflatex engine$(NC)"; \
		elif command -v wkhtmltopdf >/dev/null 2>&1; then \
			PDF_ENGINE="--pdf-engine=wkhtmltopdf"; \
			echo "$(BLUE)Using wkhtmltopdf engine$(NC)"; \
		else \
			echo "$(YELLOW)No PDF engine found - attempting to install MiKTeX for Windows...$(NC)"; \
			if [ "$$OS_NAME" = "MINGW64_NT"* ] || [ "$$OS_NAME" = "MSYS_NT"* ] || [ "$$OS_NAME" = "CYGWIN_NT"* ]; then \
				if command -v winget >/dev/null 2>&1; then \
					echo "$(BLUE)Installing MiKTeX via winget...$(NC)"; \
					winget install -e --id MiKTeX.MiKTeX --accept-package-agreements --accept-source-agreements || true; \
					echo "$(GREEN)MiKTeX installation attempted. Please restart your terminal and run make build again.$(NC)"; \
				else \
					echo "$(YELLOW)winget not found. Please install MiKTeX manually from https://miktex.org/download$(NC)"; \
				fi; \
			else \
				echo "$(YELLOW)Install PDF engine manually: $(shell if command -v brew >/dev/null 2>&1; then echo "brew install basictex"; elif command -v apt-get >/dev/null 2>&1; then echo "sudo apt-get install texlive-xetex"; else echo "Visit https://www.tug.org/texlive/"; fi)$(NC)"; \
			fi; \
			echo "$(YELLOW)Skipping PDF generation for now$(NC)"; \
		fi; \
		if [ -n "$$PDF_ENGINE" ]; then \
			for file in $(ROOT_MARKDOWN_FILES); do \
				if [ -f "$$file" ]; then \
					echo "$(BLUE)Converting $$file to PDF...$(NC)"; \
					$(PANDOC) "$$file" -o "$(PDFS_DIR)/$$(basename "$$file" .md).pdf" $$PDF_ENGINE --toc --number-sections || echo "$(YELLOW)Failed to convert $$file$(NC)"; \
				fi; \
			done; \
		fi; \
	else \
		echo "$(YELLOW)Pandoc not found - attempting installation for $$OS_NAME...$(NC)"; \
		if [ "$$OS_NAME" = "MINGW64_NT"* ] || [ "$$OS_NAME" = "MSYS_NT"* ] || [ "$$OS_NAME" = "CYGWIN_NT"* ]; then \
			if command -v winget >/dev/null 2>&1; then \
				echo "$(BLUE)Installing Pandoc via winget...$(NC)"; \
				winget install -e --id JohnMacFarlane.Pandoc --accept-package-agreements --accept-source-agreements || true; \
				echo "$(GREEN)Pandoc installation attempted. Please restart your terminal and run make build again.$(NC)"; \
			else \
				echo "$(YELLOW)winget not found. Please install Pandoc manually from https://pandoc.org/installing.html$(NC)"; \
			fi; \
		else \
			echo "$(YELLOW)Please install Pandoc manually from https://pandoc.org/installing.html$(NC)"; \
		fi; \
		echo "$(YELLOW)Skipping PDF generation for now$(NC)"; \
	fi
endef

define ensure-redis
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
endef

define vagrant-up
	@echo "$(GREEN)Starting Vagrant VM...$(NC)"
	@if ! command -v $(VAGRANT) >/dev/null 2>&1; then \
		echo "$(RED)Vagrant is not installed. Please install Vagrant first.$(NC)"; \
		exit 1; \
	fi
	@$(VAGRANT) up
	@echo "$(GREEN)Vagrant VM is ready!$(NC)"
	@echo "$(BLUE)SSH into VM: vagrant ssh$(NC)"
	@echo "$(BLUE)API will be available at: http://localhost:$(DEV_PORT)$(NC)"
endef

define run-tests
	@echo "$(GREEN)Running tests...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run pytest test/ -v --cov=pollinexus; \
	else \
		$(PYTHON) -m pytest test/ -v --cov=pollinexus; \
	fi
endef

define run-linting
	@echo "$(GREEN)Running linting...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run flake8 src/ test/; \
		$(UV) run mypy src/; \
	else \
		$(PYTHON) -m flake8 src/ test/; \
		$(PYTHON) -m mypy src/; \
	fi
endef

define run-formatting
	@echo "$(GREEN)Running formatting check...$(NC)"
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) run black --check src/ test/; \
		$(UV) run isort --check-only src/ test/; \
	else \
		$(PYTHON) -m black --check src/ test/; \
		$(PYTHON) -m isort --check-only src/ test/; \
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
	@echo "  stop        - Stop running services (local only)"
	@echo "  status      - Check service status (local only)"
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

stop:
	@echo "$(BLUE)Stopping for environment: $(ENV)$(NC)"
	@$(MAKE) stop-$(ENV)

stop-%:
	@echo "$(BLUE)Stopping for environment: $*$(NC)"
	@$(MAKE) stop-$*

status:
	@echo "$(BLUE)Status for environment: $(ENV)$(NC)"
	@$(MAKE) status-$(ENV)

status-%:
	@echo "$(BLUE)Status for environment: $*$(NC)"
	@$(MAKE) status-$*

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
	@$(call generate-pdfs)
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
	@echo "$(GREEN)Verifying Jupyter installation...$(NC)"
	@$(UV) run python -c "import jupyter; print('✓ Jupyter available')" 2>/dev/null || (echo "$(RED)✗ Jupyter not found. Installing...$(NC)" && $(UV) add jupyterlab)
	@$(call ensure-redis)
	@echo "$(GREEN)Starting FastAPI server in background...$(NC)"
	@POLLINEXUS_DISABLE_SECURITY_FOR_LOCAL=true $(UV) run uvicorn pollinexus.api.main:app \
		--host $(DEV_HOST) \
		--port $(DEV_PORT) \
		$(if $(filter true,$(DEV_RELOAD)),--reload) \
		--workers $(DEV_WORKERS) > api.log 2>&1 & \
		echo $$! > api.pid
	@sleep 2
	@echo "$(GREEN)Starting Jupyter Lab for notebooks...$(NC)"
	@$(UV) run jupyter lab --no-browser --NotebookApp.token='' --NotebookApp.password='' --ip=$(DEV_HOST) --port=8888 --notebook-dir=notebooks > jupyter.log 2>&1 & \
		echo $$! > jupyter.pid
	@sleep 3
	@echo "$(GREEN)Services started successfully!$(NC)"
	@echo "$(GREEN)FastAPI running at http://$(DEV_HOST):$(DEV_PORT)$(NC)"
	@echo "$(GREEN)Jupyter Lab running at http://$(DEV_HOST):8888$(NC)"
	@echo "$(YELLOW)Logs: api.log (FastAPI) and jupyter.log (Jupyter)$(NC)"
	@echo "$(YELLOW)To stop services: make stop-local$(NC)"
	@echo "$(YELLOW)To check status: make status-local$(NC)"

status-local:
	@echo "$(BLUE)Checking local service status...$(NC)"
	@if [ -f api.pid ] && kill -0 $$(cat api.pid) 2>/dev/null; then \
		echo "$(GREEN)✓ FastAPI server is running (PID: $$(cat api.pid))$(NC)"; \
		echo "$(BLUE)  URL: http://$(DEV_HOST):$(DEV_PORT)$(NC)"; \
		if [ -f api.log ]; then \
			echo "$(BLUE)  Log: api.log$(NC)"; \
		fi; \
	else \
		echo "$(RED)✗ FastAPI server is not running$(NC)"; \
		if [ -f api.log ]; then \
			echo "$(YELLOW)  Check api.log for errors$(NC)"; \
		fi; \
	fi
	@if [ -f jupyter.pid ] && kill -0 $$(cat jupyter.pid) 2>/dev/null; then \
		echo "$(GREEN)✓ Jupyter Lab is running (PID: $$(cat jupyter.pid))$(NC)"; \
		echo "$(BLUE)  URL: http://$(DEV_HOST):8888$(NC)"; \
		if [ -f jupyter.log ]; then \
			echo "$(BLUE)  Log: jupyter.log$(NC)"; \
		fi; \
	else \
		echo "$(RED)✗ Jupyter Lab is not running$(NC)"; \
		if [ -f jupyter.log ]; then \
			echo "$(YELLOW)  Check jupyter.log for errors$(NC)"; \
		fi; \
	fi

stop-local:
	@echo "$(GREEN)Stopping local services...$(NC)"
	@if [ -f api.pid ]; then \
		kill $$(cat api.pid) 2>/dev/null || true; \
		rm -f api.pid; \
		echo "$(GREEN)FastAPI server stopped$(NC)"; \
	fi
	@if [ -f jupyter.pid ]; then \
		kill $$(cat jupyter.pid) 2>/dev/null || true; \
		rm -f jupyter.pid; \
		echo "$(GREEN)Jupyter Lab stopped$(NC)"; \
	fi
	@echo "$(GREEN)All local services stopped$(NC)"



verify-local:
	@echo "$(GREEN)Running comprehensive verification locally...$(NC)"
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "$(RED)uv is not installed. Please install uv first.$(NC)"; \
		exit 1; \
	fi
	@$(call run-tests)
	@$(call run-linting)
	@$(call run-formatting)
	@echo "$(GREEN)Verification complete!$(NC)"

# Docker development targets
build-docker:
	@echo "$(GREEN)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache
	@$(call generate-pdfs)
	@echo "$(GREEN)Docker build complete!$(NC)"

train-docker:
	@echo "$(GREEN)Training ML models with Docker...$(NC)"
	@$(DOCKER_COMPOSE) up --build --no-deps trainer
	@echo "$(GREEN)Docker training complete!$(NC)"

run-docker:
	@echo "$(GREEN)Running application with Docker...$(NC)"
	@$(DOCKER_COMPOSE) up --build
	@echo "$(GREEN)Docker application stopped.$(NC)"

stop-docker:
	@echo "$(GREEN)Stopping Docker services...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Docker services stopped$(NC)"

status-docker:
	@echo "$(GREEN)Checking Docker service status...$(NC)"
	@$(DOCKER_COMPOSE) ps

verify-docker:
	@echo "$(GREEN)Running verification with Docker...$(NC)"
	@$(DOCKER_COMPOSE) run --rm app pytest test/ -v --cov=pollinexus
	@$(DOCKER_COMPOSE) run --rm app flake8 src/ test/
	@$(DOCKER_COMPOSE) run --rm app mypy src/
	@echo "$(GREEN)Docker verification complete!$(NC)"

# Remote deployment targets (Vagrant)
build-remote:
	@echo "$(GREEN)Building in remote VM...$(NC)"
	@$(call vagrant-up)
	@echo "$(GREEN)Installing dependencies in VM...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && uv sync --dev"
	@echo "$(GREEN)Generating PDFs from markdown files...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && if ! command -v pandoc >/dev/null 2>&1; then echo 'Pandoc not found. Attempting installation...'; sudo apt-get update && sudo apt-get install -y pandoc; fi; if command -v pandoc >/dev/null 2>&1; then mkdir -p pdfs; PDF_ENGINE=''; if command -v xelatex >/dev/null 2>&1; then PDF_ENGINE='--pdf-engine=xelatex'; elif command -v pdflatex >/dev/null 2>&1; then PDF_ENGINE='--pdf-engine=pdflatex'; elif command -v wkhtmltopdf >/dev/null 2>&1; then PDF_ENGINE='--pdf-engine=wkhtmltopdf'; else echo 'No PDF engine found - attempting to install texlive-xetex...'; sudo apt-get update && sudo apt-get install -y texlive-xetex; fi; for file in README.md; do if [ -f \"\$$file\" ]; then echo 'Converting \$$file to PDF...'; pandoc \"\$$file\" -o \"pdfs/\$$(basename \"\$$file\" .md).pdf\" \$$PDF_ENGINE --toc --number-sections; fi; done; for file in docs/*.md; do if [ -f \"\$$file\" ]; then echo 'Converting \$$file to PDF...'; pandoc \"\$$file\" -o \"pdfs/\$$(basename \"\$$file\" .md).pdf\" \$$PDF_ENGINE --toc --number-sections; fi; done; for file in docs/api-groups/*.md; do if [ -f \"\$$file\" ]; then echo 'Converting \$$file to PDF...'; pandoc \"\$$file\" -o \"pdfs/api-groups-\$$(basename \"\$$file\" .md).pdf\" \$$PDF_ENGINE --toc --number-sections; fi; done; echo 'PDFs generated in pdfs/'; else echo 'Pandoc installation failed - skipping PDF generation'; fi"
	@echo "$(GREEN)Remote build complete!$(NC)"

train-remote:
	@echo "$(GREEN)Training ML models in remote VM...$(NC)"
	@$(call vagrant-up)
	@echo "$(GREEN)Running training pipeline in VM...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run python -m pollinexus.cli train-models"
	@echo "$(GREEN)Remote training complete!$(NC)"

run-remote:
	@echo "$(GREEN)Running application in remote VM...$(NC)"
	@$(call vagrant-up)
	@echo "$(GREEN)Starting FastAPI server in VM...$(NC)"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run uvicorn pollinexus.api.main:app --host 0.0.0.0 --port $(DEV_PORT) --reload"

stop-remote:
	@echo "$(GREEN)Stopping remote VM...$(NC)"
	@$(VAGRANT) halt
	@echo "$(GREEN)Remote VM stopped$(NC)"

status-remote:
	@echo "$(GREEN)Checking remote VM status...$(NC)"
	@$(VAGRANT) status

verify-remote:
	@echo "$(GREEN)Running verification in remote VM...$(NC)"
	@$(call vagrant-up)
	@$(VAGRANT) ssh -c "cd /vagrant && uv run pytest test/ -v --cov=pollinexus"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run flake8 src/ test/"
	@$(VAGRANT) ssh -c "cd /vagrant && uv run mypy src/"
	@echo "$(GREEN)Remote verification complete!$(NC)"









clean:
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf .venv/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -f pollinexus.db
	@rm -f *.db
	@echo "$(GREEN)Clean complete!$(NC)"

clean-local:
	@echo "$(GREEN)Cleaning local artifacts...$(NC)"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -f pollinexus.db
	@rm -f *.db
	@rm -f api.pid jupyter.pid api.log jupyter.log
	@echo "$(GREEN)Local clean complete!$(NC)"

clean-docker:
	@echo "$(GREEN)Cleaning Docker artifacts...$(NC)"
	@$(DOCKER_COMPOSE) down --volumes --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)Docker clean complete!$(NC)"


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

