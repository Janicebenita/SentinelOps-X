.PHONY: setup backend frontend demo-app demo seed reset test lint typecheck security validate export benchmark clean
setup:
	python scripts/ensure_dependencies.py --setup-only
backend:
	uvicorn backend.app.main:app --reload --port 8000
frontend:
	cd frontend && pnpm dev
demo-app:
	uvicorn demo_app.app.main:app --reload --port 8001
demo:
	python scripts/ensure_dependencies.py
seed:
	python scripts/nexus_e2e.py
reset:
	curl -X POST http://127.0.0.1:8000/api/v1/demo/reset
test:
	pytest backend/tests demo_app/tests -q
	cd frontend && pnpm test
lint:
	ruff check .
typecheck:
	mypy backend demo_app scripts
security:
	bandit -q -lll -r backend demo_app scripts
validate: test lint typecheck security
	cd frontend && pnpm run build
	python scripts/nexus_e2e.py
export:
	python scripts/nexus_e2e.py
benchmark:
	python scripts/benchmark.py
health:
	python scripts/health_check.py
clean:
	docker compose down
