# HR Agent Backend Makefile

.PHONY: help install test setup dev prod clean docker-build docker-up docker-down migrate reset-db

# Default target
help:
	@echo "HR Agent Backend - Available Commands:"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  install     - Install Python dependencies"
	@echo "  setup       - Setup development environment"
	@echo "  test-setup  - Test the setup and configuration"
	@echo ""
	@echo "Development:"
	@echo "  dev         - Start development server"
	@echo "  prod        - Start production server"
	@echo "  test        - Run tests"
	@echo ""
	@echo "Database:"
	@echo "  migrate     - Create and apply database migrations"
	@echo "  reset-db    - Reset database (drop and recreate)"
	@echo "  init-db     - Initialize database"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up   - Start services with Docker Compose"
	@echo "  docker-down - Stop Docker services"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean       - Clean temporary files"
	@echo "  format      - Format code with black"
	@echo "  lint        - Run linting with flake8"

# Installation and setup
install:
	pip install -r requirements.txt

setup: install
	@echo "Setting up development environment..."
	@if not exist .env (copy .env.example .env && echo "Created .env file from .env.example")
	@if not exist logs (mkdir logs)
	@if not exist uploads (mkdir uploads)
	@if not exist temp (mkdir temp)
	@echo "Development environment setup complete!"

test-setup:
	python scripts/test_setup.py

# Development
dev:
	python scripts/start.py dev

prod:
	python scripts/start.py prod

test:
	pytest tests/ -v

# Database operations
init-db:
	python scripts/db_manager.py init

migrate:
	python scripts/db_manager.py migrate "Auto migration"
	python scripts/db_manager.py upgrade

reset-db:
	python scripts/db_manager.py reset

# Docker operations
docker-build:
	docker build -t hr-agent-backend .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f backend

# Code quality
format:
	black app/ scripts/ main.py
	isort app/ scripts/ main.py

lint:
	flake8 app/ scripts/ main.py
	mypy app/ scripts/ main.py

# Maintenance
clean:
	@echo "Cleaning temporary files..."
	@if exist __pycache__ (rmdir /s /q __pycache__)
	@if exist .pytest_cache (rmdir /s /q .pytest_cache)
	@if exist .mypy_cache (rmdir /s /q .mypy_cache)
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@for /d /r . %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
	@echo "Cleanup complete!"

# Quick start for new developers
quickstart: setup init-db test-setup
	@echo ""
	@echo "🎉 HR Agent Backend is ready!"
	@echo ""
	@echo "To start development:"
	@echo "  make dev"
	@echo ""
	@echo "To view API documentation:"
	@echo "  Open http://localhost:8000/api/v1/docs"