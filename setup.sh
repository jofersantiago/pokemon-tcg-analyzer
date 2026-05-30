#!/usr/bin/env bash
# One-time setup: creates a virtual environment and installs all dependencies.
# Run this once after cloning or unzipping the project, then use python3 main.py.
set -e

echo "Creating virtual environment..."
python3 -m venv venv

echo "Installing dependencies..."
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q

echo ""
echo "Setup complete!"
echo "Run the app with:  python3 main.py"
