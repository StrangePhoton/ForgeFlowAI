#!/bin/sh
set -eu

echo "running database migrations"
alembic upgrade head

echo "starting api"
exec uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
