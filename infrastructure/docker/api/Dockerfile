FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system forgeflow \
    && useradd --system --gid forgeflow --create-home forgeflow

COPY pyproject.toml README.md alembic.ini /app/
COPY forgeflow /app/forgeflow
COPY apps /app/apps
COPY infrastructure/docker/api/entrypoint.sh /app/infrastructure/docker/api/entrypoint.sh

RUN pip install --no-cache-dir . \
    && chmod +x /app/infrastructure/docker/api/entrypoint.sh \
    && chown -R forgeflow:forgeflow /app

USER forgeflow

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=10 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3)"

ENTRYPOINT ["/app/infrastructure/docker/api/entrypoint.sh"]
