.PHONY: install run test lint format migrate db-up db-down clean help

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run the application"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting"
	@echo "  make format     - Format code"
	@echo "  make migrate    - Run database migrations"
	@echo "  make db-up      - Start TiDB with Docker Compose"
	@echo "  make db-down    - Stop TiDB"
	@echo "  make clean      - Clean up cache and build files"

install:
	pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

migrate:
	alembic upgrade head

db-up:
	docker-compose up -d

db-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov
