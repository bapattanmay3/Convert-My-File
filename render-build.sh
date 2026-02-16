#!/usr/bin/env bash
# render-build.sh - Forces pip install to run and succeed

set -e  # exit on error

echo "Installing dependencies with pip..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn # Explicitly ensuring gunicorn is available

echo "Verifying gunicorn installation..."
python -m gunicorn --version

echo "Build script completed successfully."
