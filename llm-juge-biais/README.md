# The LLM judge that prefers the longest answer

The bench of the deck https://heurisme.fr/en/blog/llm-juge-biais/ : 30 pairs of technical answers (written by hand, no real data) judged by two small models, with 5 protocols, to measure length bias and position bias.

File names and part of the outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `banc/` = bench, `paires.py` = pairs, `juge.py` = judge, `analyse.py` = analysis, `brut.py` = raw (shows a raw call), `tout.sh` = run everything, `tourne.sh` = run one command and save its output, `verdicts/` = verdicts, `sorties/` = outputs (French), `sorties-en/` = outputs (English). Protocols: `naif` = naive, `egalite` = tie allowed, `grille` = grid, `reference` = reference answer, `note` = score. Analyses: `ordre` = order, `longueur` = length, `parades` = countermeasures, `notes` = scores.

## How to replay

- Python 3.13 with mlx-lm 0.31.3 (PyPI, 2026-04-22; Apple Silicon Mac: MLX). The script creates `.venv`.
- Qwen2.5-7B-Instruct 4-bit: `mlx-community/Qwen2.5-7B-Instruct-4bit` on Hugging Face, downloaded by `huggingface_hub` (snapshot used: `c26a38f6a37d0a51b4e9a1eb3026530fa35d9fed`). Greedy decoding.
- Ollama 0.30.10 (release of 2026-06-17, archive `ollama-darwin.tgz` from https://github.com/ollama/ollama/releases/tag/v0.30.10) with phi4 (14.7 B, Q4_K_M, published in December 2024): `ollama pull phi4`. Temperature 0, seed 0. Server settings used: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, the rest at the defaults of this version. `banc/juge.py` calls `127.0.0.1:11434`, or the URL given in `OLLAMA_URL` (the phi4 verdicts here come from a separate server on `127.0.0.1:11500`).
- Allow 1 to 2 hours for the 10 runs (2 judges, 5 protocols, sequential).

Single command:

```bash
bash rejouer.sh
```

It installs mlx-lm, fetches the two models, runs `banc/tout.sh` (writes `banc/verdicts/*.jsonl`, one full call per line: prompt, raw output, parsed verdict), then `banc/deck.sh` (writes `banc/sorties/` in French and `banc/sorties-en/` in English).

## File to slide

| File | Slide |
|---|---|
| `banc/paires.py` → `banc/paires.json`, `banc/sorties/10-paires.txt` | 2 |
| `banc/juge.py` → `banc/verdicts/*.jsonl`, `banc/sorties/01-*` to `05-*` | 3 to 10 |
| `banc/analyse.py ordre` → `banc/sorties/15-analyse-ordre.txt` | 3, 4 |
| `banc/analyse.py longueur` → `banc/sorties/15-analyse-longueur.txt` | 5 |
| `banc/brut.py paire 28` → `banc/sorties/13-fausses.txt` | 6 |
| `banc/brut.py qwen grille 7 BA` → `banc/sorties/14-brut-grille-7.txt` | 7 |
| `banc/brut.py phi4 grille 1 AB` → `banc/sorties/16-brut-phi4-grille-1.txt` | 8 |
| `banc/analyse.py parades` → `banc/sorties/15-analyse-parades.txt` | 9 |
| `banc/analyse.py notes` → `banc/sorties/15-analyse-notes.txt` | 10 |

`banc/tourne.sh` runs a command and stores its output in `sorties/` (or `sorties-en/`). `banc/verdicts-en/qwen-naif.jsonl` is the rerun of Qwen in English: the judge outputs are identical to the French run.

## Third-party data

- Reference paper of the deck: Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", https://arxiv.org/abs/2306.05685 (PDF https://arxiv.org/pdf/2306.05685, sha256 `15749828…cb81`). Not copied here: the bench does not need it, the deck cites it.
- Models: see above, downloaded by `rejouer.sh`.
