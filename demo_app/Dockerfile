FROM python:3.12-slim
WORKDIR /workspace
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY demo_app demo_app
CMD ["uvicorn", "demo_app.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
