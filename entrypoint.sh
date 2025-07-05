#!/bin/sh

set -e

echo "Waiting for postgres..."

# Wait for PostgreSQL to be ready
until nc -z postgres 5432; do
  echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "Postgres is up - continuing"

# Run Django management commands
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# Start the server
exec python manage.py runserver 0.0.0.0:8000
