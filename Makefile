.PHONY: setup backend frontend demo-app demo seed reset test lint typecheck security benchmark clean
setup:
	python scripts/ensure_dependencies.py --setup-only
backend:
	uvicorn backend.app.main:app --reload --port 8000
frontend:
	cd frontend && npm run dev
demo-app:
	uvicorn demo_app.app.main:app --reload --port 8001
demo:
	python scripts/ensure_dependencies.py
seed:
	python scripts/seed_incident.py
reset:
	python scripts/reset_demo.py
test:
	pytest --cov=backend --cov=demo_app
	cd frontend && npm test
lint:
	ruff check .
typecheck:
	mypy backend demo_app
security:
	bandit -q -lll -r backend demo_app
benchmark:
	python scripts/benchmark.py
health:
	python scripts/health_check.py
clean:
	docker compose down
