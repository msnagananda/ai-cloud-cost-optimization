#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code on the web environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Install Python backend dependencies
if [ -f "$PROJECT_DIR/backend/requirements.txt" ]; then
  echo "Installing Python backend dependencies..."
  pip install -r "$PROJECT_DIR/backend/requirements.txt"
fi

# Install Node.js frontend dependencies
if [ -f "$PROJECT_DIR/frontend/package.json" ]; then
  echo "Installing Node.js frontend dependencies..."
  cd "$PROJECT_DIR/frontend"
  npm install
  cd "$PROJECT_DIR"
fi

echo "Session start setup complete."
