.PHONY: help install check test lint run build up down logs

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "; print "Usage: make <target>\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install application and development dependencies
	python -m pip install -e '.[dev]'

check: lint test ## Run all local quality checks

test: ## Run the automated test suite
	python -m pytest -q

lint: ## Run static lint checks
	python -m ruff check .

run: ## Start the browser app locally
	streamlit run streamlit_app.py

build: ## Build the production container
	docker build --tag tweet-audit:local .

up: ## Start the hardened container stack
	docker compose up --build --detach

down: ## Stop the container stack
	docker compose down

logs: ## Follow application logs
	docker compose logs --follow web

