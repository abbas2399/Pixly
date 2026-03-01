#!/bin/sh
set -e

echo "=== Running migrations ==="
python manage.py migrate --noinput
echo "=== Starting gunicorn on port ${PORT:-8080} ==="
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 1 \
    --timeout 120 \
    --log-level info \
    --access-logfile -
