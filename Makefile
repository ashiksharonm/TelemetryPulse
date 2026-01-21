.PHONY: up down test lint

up:
	docker-compose up -d --build

down:
	docker-compose down

test:
	pytest tests/

lint:
	# Placeholder for linting
	echo "Linting..."
