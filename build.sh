#!/usr/bin/env bash
# Build step for production hosts (Render/Railway). Exit on any error.
set -o errexit

pip install -r requirements.txt

# Collect static files for WhiteNoise to serve.
python manage.py collectstatic --no-input

# Apply database migrations.
python manage.py makemigrations --no-input
python manage.py migrate --no-input
