FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY backend backend
COPY demo_app demo_app
RUN pip install --no-cache-dir .
ENV PRODUCTION_EXECUTION=false
EXPOSE 8000
CMD ["uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000"]
