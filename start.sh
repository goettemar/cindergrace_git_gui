#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./start.sh [--refresh] [--no-dev]

Options:
  --refresh   Reinstall dependencies even if already installed
  --no-dev    Install only runtime dependencies (skip dev extras)
USAGE
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
MARKER_FILE="$VENV_DIR/.cindergrace_git_gui_installed"

REFRESH=0
NO_DEV=0

for arg in "$@"; do
  case "$arg" in
    --refresh) REFRESH=1 ;;
    --no-dev) NO_DEV=1 ;;
    *)
      echo "Unknown option: $arg"
      usage
      exit 1
      ;;
  esac
done

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating venv..."
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if [ ! -f "$MARKER_FILE" ] || [ "$REFRESH" -eq 1 ]; then
  echo "Installing dependencies..."
  python -m pip install --upgrade pip
  if [ "$NO_DEV" -eq 1 ]; then
    python -m pip install -e .
  else
    python -m pip install -e ".[dev]"
  fi
  touch "$MARKER_FILE"
fi

python main.py
