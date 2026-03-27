.PHONY: up down restart logs reset status shell build clean

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

reset:
	docker compose down -v
	docker compose up -d

status:
	docker compose ps

shell:
	docker compose exec airflow-api-server bash

build:
	docker compose build --no-cache

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf logs/*
