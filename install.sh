#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install litellm "agno[all]" fastapi uvicorn openai

if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
ollama pull qwen3:8b
ollama pull bge-m3

echo "Setup complete. cp .env.example .env, fill in keys, then:"
echo "  litellm --config litellm.yaml.example --port 4000"
echo "  npm-free: venv/bin/python team.py"
echo "  Telegram: give your bot token to TELEGRAM_BOT_TOKEN, run team.py"