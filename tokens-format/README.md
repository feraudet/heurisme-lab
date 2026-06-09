# JSON, YAML or CSV: what a prompt costs

The bench of the deck https://heurisme.fr/en/blog/tokens-format/ : the same inventory of 100 servers (invented, fixed seed) written in 6 formats, counted in tokens with 4 tokenizers, then used as the basis for questions to phi4.

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `banc/` = bench, `data/` = data, `inventaire.*` = inventory, `decouper.py` = split, `compter.py` = count, `langues.py` = languages, `nombres.py` = numbers, `qualite.py` = quality, `ratios.py` = ratios. In `data/`, the `*.en.txt` files are the English outputs and the files without `.en` are the French ones (format names like `json-indente` = json-indented, `json-minifie` = json-minified).

## How to replay

- Python 3.12 and `uv` (the script creates `.venv`), `curl`, `shasum`.
- Packages (see `banc/requirements.txt`): tiktoken 0.13.0 (2026-05-15), tokenizers 0.23.1 (2026-04-27), PyYAML 6.0.3.
- Ollama 0.30.7 (release of 2026-06-07, archive `ollama-darwin.tgz` from https://github.com/ollama/ollama/releases/tag/v0.30.7) with `phi4` (14.7 B, Q4_K_M, published in December 2024): the script runs `ollama pull phi4`. Server settings used: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, the rest at the defaults of this version. `banc/qualite.py` calls `localhost:11434`, or the URL given in `OLLAMA_URL` (the outputs here come from a separate server on `127.0.0.1:11500`). The quality test takes a while (60 questions, free answers up to 1024 tokens).

Single command:

```bash
bash banc/rejouer.sh
```

The script downloads the third-party data (sha256 checked), regenerates `data/inventaire.*`, all the `data/*.txt` outputs (French) and `data/*.en.txt` (English), then reruns the quality test. It creates an Ollama alias `phi4-banc` (same weights as `phi4`, `num_ctx` 16384, see `banc/Modelfile.phi4-banc`); run `ollama rm phi4-banc` to remove it.

## File to slide

| File | Slide |
|---|---|
| `banc/gen_data.py` → `data/inventaire.{json,min.json,yaml,csv,md,xml}` | 2 |
| `banc/decouper.py` → `data/decouper.txt` | 3 |
| `banc/compter.py` → `data/compter.txt`, `data/comptes.json` | 4, 9 |
| `banc/langues.py` → `data/langues.txt` | 5 |
| `banc/nombres.py` → `data/nombres.txt` | 6 |
| `banc/qualite.py` → `data/qualite.jsonl`, `data/qualite.log`, `data/bilan.txt` | 7, 9 |
| `banc/ratios.py` → `data/ratios.txt` | 8 |

`banc/tok.py` and `banc/langue.py` are shared modules. `banc/qualite.py` grades the answers automatically (function `retenue()`): two cases are debatable, slide 7 shows them.

## Third-party data (downloaded by `banc/rejouer.sh`, never copied here)

- `o200k_base` vocabulary: https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken (sha256 `446a9538…1a2d`).
- `cl100k_base` vocabulary: https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken (sha256 `223921b7…b2a7`).
- Qwen2.5 tokenizer: `tokenizer.json` of the model `mlx-community/Qwen2.5-7B-Instruct-4bit`, revision `c26a38f6a37d0a51b4e9a1eb3026530fa35d9fed` (sha256 `a8506e71…61bf`). The deck points to the original model `Qwen/Qwen2.5-7B-Instruct`. Model license: Apache 2.0.
- The phi4 model comes from Ollama (`ollama pull phi4`), MIT license.
