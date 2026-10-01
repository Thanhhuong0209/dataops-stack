FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DAGSTER_HOME=/opt/dagster/dagster_home \
    VICTORIAMETRICS_URL=http://victoriametrics:8428 \
    APP_PORT=3030

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY dagster_pipeline.py ./
COPY vm_ingestion_test.py ./

RUN mkdir -p data "$DAGSTER_HOME" && touch data/__init__.py

EXPOSE 3030

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=5 \
  CMD python -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('127.0.0.1', int(__import__('os').environ.get('APP_PORT', '3030')))); s.close()" || exit 1

CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "3030", "-f", "dagster_pipeline.py"]
