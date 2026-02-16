#!/usr/bin/env bash
# render-build.sh - Forces pip install to run and succeed

set -e  # exit on error

echo "Installing dependencies with pip..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Build script completed successfully."
