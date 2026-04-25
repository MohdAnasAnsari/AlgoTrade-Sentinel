.PHONY: dev prod build migrate seed test lint deploy down

dev:
	docker compose -f docker-compose.dev.yml up --build

prod:
	docker compose -f docker-compose.yml up --build

build:
	docker compose -f docker-compose.yml build

migrate:
	docker compose -f docker-compose.yml run --rm backend /bin/sh /app/scripts/init_db.sh

seed:
	docker compose -f docker-compose.yml run --rm backend /bin/sh /app/scripts/seed_data.sh

test:
	cd frontend && npm run lint && npm run type-check
	cd backend && python -m pytest -v

lint:
	cd frontend && npm run lint && npm run type-check
	cd backend && python -m ruff check app tests && python -m mypy app/main.py app/config.py app/database.py app/middleware.py app/scheduler.py app/services/system_service.py app/routers/system.py tests

deploy:
	gh workflow run deploy.yml

down:
	docker compose -f docker-compose.yml down -v
