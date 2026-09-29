#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" 2>/dev/null || true
fi

# TEMP-DEBUG: access-logfile/error-logfile/log-level debug -- remover quando o diagnostico terminar
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 \
    --access-logfile - --error-logfile - --log-level debug \
    --access-logformat '%(t)s "%(r)s" status=%(s)s bytes=%(b)s reqtime=%(L)ss'
