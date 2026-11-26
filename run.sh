#!/usr/bin/env bash
# run.sh - one-command local setup + launch for Project Overlord (macOS/Linux).
#
#   ./run.sh          # create .venv, install deps, start the UI on :7860
#   ./run.sh --test   # install dev deps and run pytest
#   ./run.sh --docker # build and run the container instead
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-7860}"

if [[ "${1:-}" == "--docker" ]]; then
  docker build -t zerotouch-ap-auditor:local .
  docker run --rm -p "${PORT}:7860" --env-file .env -v "$PWD/workspace:/app/workspace" \
    zerotouch-ap-auditor:local
  exit $?
fi

if [[ ! -d .venv ]]; then
  echo "Creating virtualenv ..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip --quiet

if [[ "${1:-}" == "--test" ]]; then
  python -m pip install -r requirements-dev.txt --quiet
  exec python -m pytest
fi

python -m pip install -r requirements.txt --quiet

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example - add HF_TOKEN to turn on Gemma 4."
fi

export GRADIO_SERVER_PORT="$PORT"
echo "Starting Project Overlord on http://127.0.0.1:$PORT"
exec python app.py
