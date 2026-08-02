FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 runner
WORKDIR /workspace
RUN pip install --no-cache-dir 'fastapi<1' 'uvicorn<1' 'pydantic<3' 'pydantic-settings<3' \
    'sqlalchemy<3' 'httpx<1' 'python-json-logger<4' 'pyyaml<7' 'pytest<9' \
    'pytest-cov<7' 'ruff<1' 'mypy<2' 'bandit<2'
COPY sandbox/entrypoint.py /opt/entrypoint.py
USER runner
ENTRYPOINT ["python", "/opt/entrypoint.py"]
