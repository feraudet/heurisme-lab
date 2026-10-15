#!/bin/bash
# Replays the bench of the deck https://heurisme.fr/en/blog/tokens-francais-anglais/
# Needs curl, shasum and Docker. Downloads the third-party files (tokenizer vocabularies, the parallel corpus)
# into telechargements/, checks each sha256, then counts the tokens in a python:3.12-slim-bookworm container
# pinned by digest, with tiktoken 0.13.0, tokenizers 0.23.1 and regex 2026.9.29 (pip, exact versions).
set -eu
cd "$(dirname "$0")"

tel() {  # tel <url> <destination> <sha256>
  mkdir -p "$(dirname "$2")"
  [ -f "$2" ] || curl -fsSL "$1" -o "$2"
  echo "$3  $2" | shasum -a 256 -c - >/dev/null || { echo "sha256 mismatch: $2" >&2; exit 1; }
}

# tiktoken vocabularies (OpenAI). The cache file name is the sha1 of the URL, as tiktoken expects.
T=https://openaipublic.blob.core.windows.net/encodings
tel $T/cl100k_base.tiktoken telechargements/tiktoken/9b5ad71b2ce5302211f9c61530b329a4922fc6a4 223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7
tel $T/o200k_base.tiktoken  telechargements/tiktoken/fb374d419588a4632f3f557e76b4b70aebbca790 446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d

# Hugging Face tokenizers, each at a pinned repo revision (commit hash).
H=https://huggingface.co
tel $H/mistralai/Mistral-7B-Instruct-v0.3/resolve/c170c708c41dac9275d15a8fff4eca08d52bab71/tokenizer.json \
  telechargements/mistral-7b-v0.3.json e553af6fff7d7ad76e830608b218c5c0b0822998d5a1a96099a74cd3c1cb1a49
tel $H/mistralai/Mistral-Nemo-Instruct-2407/resolve/04d8a90549d23fc6bd7f642064003592df51e9b3/tokenizer.json \
  telechargements/mistral-nemo.json e11c71726323d33da7b8d6f6f269f1988931c0a52b7122bcdd8c05042974e0db
tel $H/Qwen/Qwen2.5-7B-Instruct/resolve/a09a35458c702b33eeacc393d103063234e8bc28/tokenizer.json \
  telechargements/qwen2.5.json c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539
tel $H/croissantllm/CroissantLLMBase/resolve/47baabdf7ed66de1d33e159e62a5aa947c7e2553/tokenizer.json \
  telechargements/croissantllm.json b028de04ca166adca7f1394d44599732c437387b21cc14ba236ac1f56198cf7f

# Parallel corpus: the French translation of the Python docs, commit dda0482a of branch 3.13.
P=https://raw.githubusercontent.com/python/python-docs-fr/dda0482a5960c8ede02857231a94aa8c61be35e8
D=telechargements/python-docs-fr
tel $P/tutorial/errors.po       $D/tutorial/errors.po       195f3dd167f9fe4385d0a87b72b4e76b3b0187f644dd0fa13ee6d648ce48811e
tel $P/tutorial/introduction.po $D/tutorial/introduction.po 7ed4ee67e5afe499a6da1b3271aa605c03f539e680187b9ab7a658e9d0a6ee29
tel $P/library/logging.po       $D/library/logging.po       28ce850d21c67676855245aad4b71029333d504e7534460c2536a91aa668043c
tel $P/howto/logging.po         $D/howto/logging.po         e662e514644091dcb4b90ac7d5e8d148d4ad6a9c2d1b52c7056af177d0dc9d1e
tel $P/library/subprocess.po    $D/library/subprocess.po    16ec1d4ff2ddc98315519c701d477ffa2dcadbea640341e63613c62a55cd9b0b
tel $P/glossary.po              $D/glossary.po              a2abdd10d9be2aaafdb9c152cc67fbb86b3979816aaa290c45451df21b445bbf

# Container: Python 3.12 on Debian 12, arm64 (remove --platform on an x86_64 machine).
IMAGE=python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
docker run --rm --platform linux/arm64 --network bridge -v "$PWD":/w "$IMAGE" bash /w/calcule.sh

echo "Outputs in sorties/. Compare with git diff."
