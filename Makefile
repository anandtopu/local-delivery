.PHONY: dev stop clean migrate migrate-create migrate-down seed test-backend test-frontend lint format type-check build k8s-deploy-dev k8s-deploy-staging k8s-deploy-prod shell-backend shell-db help

# ─── Local dev ────────────────────────────────────────────────────────────────
dev:                          ## Start full stack (docker compose up --build)
	docker compose up -d --build

stop:                         ## Stop all services
	docker compose stop

clean:                        ## Stop + remove all volumes (DESTRUCTIVE)
	docker compose down -v --remove-orphans

# ─── Database ─────────────────────────────────────────────────────────────────
migrate:                      ## Run pending Alembic migrations
	docker compose exec backend alembic upgrade head

migrate-create:               ## Auto-generate migration: make migrate-create MSG="add_column"
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down:                 ## Rollback last migration
	docker compose exec backend alembic downgrade -1

seed:                         ## Seed database with sample data
	docker compose exec backend python scripts/seed_data.py

# ─── Testing ──────────────────────────────────────────────────────────────────
test-backend:                 ## Run backend pytest suite
	docker compose exec backend pytest tests/ -v

test-backend-cov:             ## Run backend tests with HTML coverage
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

test-frontend:                ## Run frontend vitest suite
	docker compose exec frontend npm run test

test-e2e:                     ## Run Playwright e2e tests
	docker compose exec frontend npx playwright test

# ─── Code quality ─────────────────────────────────────────────────────────────
lint:                         ## Run ruff + eslint
	docker compose exec backend ruff check app/ tests/
	docker compose exec frontend npm run lint

format:                       ## Run ruff format + prettier
	docker compose exec backend ruff format app/ tests/
	docker compose exec frontend npx prettier --write src/

type-check:                   ## Run mypy + tsc
	docker compose exec backend mypy app/
	docker compose exec frontend npm run type-check

# ─── Build ────────────────────────────────────────────────────────────────────
build:                        ## Build production Docker images
	docker build --target production -t local-delivery/backend:latest ./backend
	docker build --target production -t local-delivery/frontend:latest ./frontend

# ─── Kubernetes ───────────────────────────────────────────────────────────────
k8s-deploy-dev:               ## Deploy to dev namespace
	kubectl apply -k k8s/overlays/dev

k8s-deploy-staging:           ## Deploy to staging namespace
	kubectl apply -k k8s/overlays/staging

k8s-deploy-prod:              ## Deploy to prod namespace
	kubectl apply -k k8s/overlays/prod

k8s-status:                   ## Show pods, services, ingress
	kubectl get pods,svc,ingress -n local-delivery

# ─── Shells ───────────────────────────────────────────────────────────────────
shell-backend:                ## Open bash in backend container
	docker compose exec backend bash

shell-db:                     ## Open psql in postgres container
	docker compose exec postgres psql -U delivery_user -d local_delivery

# ─── Help ─────────────────────────────────────────────────────────────────────
help:                         ## Show all commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
