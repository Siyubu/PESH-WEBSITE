#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
# Adds the bundled courses on first run; never overwrites lessons edited in the admin.
python manage.py import_courses --only-new
python manage.py import_exams --only-new

if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput --full_name "Admin" 2>/dev/null || true
fi

exec "$@"
