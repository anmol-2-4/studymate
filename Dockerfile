FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend backend
COPY frontend frontend
COPY demo demo

# COGNEE_BASE_URL and COGNEE_API_KEY come from the host environment
CMD uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8300}
