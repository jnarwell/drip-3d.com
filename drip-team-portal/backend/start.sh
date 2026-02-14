#!/bin/bash
set -e

echo "=== START SCRIPT EXECUTING ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Alembic version: $(alembic --version)"

echo "=== Running database migrations ==="
alembic current
alembic upgrade head
echo "=== Migration complete ==="

echo "=== Starting server ==="
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
