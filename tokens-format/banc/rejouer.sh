#!/usr/bin/env bash
# Replay the whole bench from the deck folder. Ollama must be running locally with phi4.
set -euo pipefail
cd "$(dirname "$0")/.."

# Third-party data: downloaded here, never copied into the repo. Each file is checked by sha256.
tel() {  # tel <url> <destination> <sha256>
  mkdir -p "$(dirname "$2")"
  [ -f "$2" ] || curl -fsSL "$1" -o "$2"
  echo "$3  $2" | shasum -a 256 -c -
}
T=https://openaipublic.blob.core.windows.net/encodings
tel $T/cl100k_base.tiktoken telechargements/tiktoken/9b5ad71b2ce5302211f9c61530b329a4922fc6a4 223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7
tel $T/o200k_base.tiktoken  telechargements/tiktoken/fb374d419588a4632f3f557e76b4b70aebbca790 446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d
tel https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit/resolve/c26a38f6a37d0a51b4e9a1eb3026530fa35d9fed/tokenizer.json telechargements/qwen2.5-tokenizer.json a8506e7111b80c6d8635951a02eab0f4e1a8e4e5772da83846579e97b16f61bf
ollama pull phi4
uv venv -q .venv --python 3.12 && uv pip install -q --python .venv/bin/python -r banc/requirements.txt
P=.venv/bin/python
$P banc/gen_data.py
for s in decouper compter langues nombres; do
  $P banc/$s.py > data/$s.txt
  $P banc/$s.py --lang en > data/$s.en.txt
done
ollama create phi4-banc -f banc/Modelfile.phi4-banc   # alias of phi4, same weights, num_ctx 16384
rm -f data/qualite.jsonl                             # otherwise qualite.py resumes where it stopped
$P banc/qualite.py | tee data/qualite.log
$P banc/qualite.py --bilan > data/bilan.txt
$P banc/qualite.py --bilan --lang en > data/bilan.en.txt
$P banc/ratios.py > data/ratios.txt
$P banc/ratios.py --lang en > data/ratios.en.txt
