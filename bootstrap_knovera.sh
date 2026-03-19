#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${ROOT_DIR}"

if [[ ! -f "${APP_DIR}/requirements.txt" ]]; then
  echo "Error: ${APP_DIR} does not look like the knovera project root."
  exit 1
fi

cd "${APP_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required but not found."
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  echo "[1/6] Creating virtual environment"
  python3 -m venv .venv
else
  echo "[1/6] Virtual environment already exists"
fi

echo "[2/6] Activating virtual environment"
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[3/6] Installing dependencies"
if ! python3 -m pip --version >/dev/null 2>&1; then
  python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
fi
python3 -m pip install --upgrade pip >/dev/null
python3 -m pip install -r requirements.txt

if [[ ! -f ".env" ]]; then
  echo "[4/6] Creating .env from .env.example"
  cp .env.example .env
else
  echo "[4/6] Using existing .env"
fi

echo "[5/6] Loading environment variables"
while IFS= read -r line || [[ -n "${line}" ]]; do
  line="${line#"${line%%[![:space:]]*}"}"
  [[ -z "${line}" || "${line}" == \#* ]] && continue
  [[ "${line}" != *=* ]] && continue

  key="${line%%=*}"
  value="${line#*=}"
  key="${key//[[:space:]]/}"

  if [[ ! "${key}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    continue
  fi

  if [[ "${value}" =~ ^\".*\"$ ]]; then
    value="${value:1:${#value}-2}"
  fi
  if [[ "${value}" =~ ^\'.*\'$ ]]; then
    value="${value:1:${#value}-2}"
  fi

  export "${key}=${value}"
done < .env

# Force-disable Chroma telemetry unless explicitly overridden.
export ANONYMIZED_TELEMETRY="${ANONYMIZED_TELEMETRY:-FALSE}"

mkdir -p "${DATA_DIR:-./data}/uploads" "${DATA_DIR:-./data}/chroma"

if [[ "${BOOTSTRAP_OLLAMA:-0}" == "1" ]]; then
  if command -v ollama >/dev/null 2>&1; then
    if ! curl -fsS "${OLLAMA_BASE_URL:-http://localhost:11434}/api/tags" >/dev/null 2>&1; then
      echo "Starting Ollama in background (log: /tmp/knovera-ollama.log)"
      nohup ollama serve >/tmp/knovera-ollama.log 2>&1 &
      sleep 2
    fi
    echo "Pulling Ollama model: ${OLLAMA_MODEL:-qwen2.5:1.5b-instruct}"
    ollama pull "${OLLAMA_MODEL:-qwen2.5:1.5b-instruct}"
  else
    echo "Warning: BOOTSTRAP_OLLAMA=1 but 'ollama' command was not found. Skipping."
  fi
else
  echo "Skipping Ollama setup (set BOOTSTRAP_OLLAMA=1 to enable)"
fi

echo "[6/6] Starting app at http://127.0.0.1:8000"
exec python3 -m uvicorn app.main:app --reload
