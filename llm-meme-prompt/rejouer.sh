#!/bin/bash
# Replay the whole bench. No third-party data to download: only the phi4 model, through Ollama 0.20.7.
# The Ollama server must run with OLLAMA_DEBUG=1 and write its log to $OLLAMA_LOG (prompt cache, step 12).
# OLLAMA_URL (default http://localhost:11434) points the scripts to another server.
set -e
cd "$(dirname "$0")"
U=${OLLAMA_URL:-http://localhost:11434}
OLLAMA_HOST=${U#http://} ollama pull phi4
curl -fsS "$U/api/version" >/dev/null || { echo "Ollama ne répond pas sur $U"; exit 1; }
bash banc/tout.sh
