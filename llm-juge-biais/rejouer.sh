#!/bin/bash
# Replay the whole bench: 30 pairs x 5 protocols x 2 judges (Qwen2.5 via mlx_lm, phi4 via Ollama).
set -e
cd "$(dirname "$0")"
python3 -m venv .venv && .venv/bin/pip install -q mlx-lm==0.31.3
export PATH="$PWD/.venv/bin:$PATH"
ollama pull phi4
python3 -c "from huggingface_hub import snapshot_download; snapshot_download('mlx-community/Qwen2.5-7B-Instruct-4bit')"
cd banc
./tout.sh
./deck.sh
