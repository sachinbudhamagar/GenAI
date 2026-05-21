.PHONY: install dev run test lint format typecheck clean

# ── Setup ────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt

# ── Run ──────────────────────────────────────────────────────
run:
	streamlit run app.py

# ── Quality ──────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	black src/ tests/ app.py

typecheck:
	mypy src/

# ── Clean ────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage
