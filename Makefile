# SIGTPI — Development commands

.PHONY: up down reset init logs ps

## Start services (preserves database data)
up:
	docker compose up -d

## Stop services (preserves database data)
down:
	docker compose down

## Initialize database (safe: adds missing tables/columns, skips if data exists)
init:
	docker compose run --rm auth-service python3 -m app.init_db

## Force re-seed (WARNING: clears all data)
seed-force:
	docker compose run --rm auth-service python3 -m app.init_db --force

## Full reset: stop, delete volumes, rebuild, start, init
reset:
	docker compose down -v --remove-orphans
	docker compose build --no-cache
	docker compose up -d
	@echo "Waiting 10s for services to start..."
	@sleep 10
	docker compose run --rm auth-service python3 -m app.init_db

## Show logs
logs:
	docker compose logs -f --tail=50

## Show service status
ps:
	docker compose ps
