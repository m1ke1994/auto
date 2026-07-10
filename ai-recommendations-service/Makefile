.PHONY: up down clean logs test lint migrate
up:
	docker compose up -d --build
down:
	docker compose down
clean:
	docker compose down -v
logs:
	docker compose logs -f api worker
test:
	pytest
lint:
	ruff check .
migrate:
	alembic upgrade head

