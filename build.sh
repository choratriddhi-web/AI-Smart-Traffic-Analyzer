#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> Upgrading pip..."
pip install --upgrade pip

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Syncing camera video assets to static directory..."
mkdir -p static/cameras
cp media/cameras/*.mp4 static/cameras/ 2>/dev/null || true

echo "==> Running Django database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static assets for WhiteNoise..."
python manage.py collectstatic --noinput

echo "==> Deployment build completed successfully!"
