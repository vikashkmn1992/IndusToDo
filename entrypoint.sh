#!/bin/bash

set -e

echo "Running Django migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Seeding database..."
python manage.py seed_data

echo "Starting Gunicorn..."
gunicorn --config gunicorn_config.py config.wsgi:application
