#!/usr/bin/env bash
set -e

cd /app

echo "Running makemigrations..."
python manage.py makemigrations

echo "Applying migrations..."
python manage.py migrate

echo "Starting server"
#python manage.py runserver 0.0.0.0:8000
daphne -b 0.0.0.0 -p 8000 proscientia.asgi:application