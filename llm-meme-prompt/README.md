# Same prompt, two answers

The bench of the deck https://heurisme.fr/en/blog/llm-meme-prompt/ : even at temperature 0, an LLM served by Ollama can answer the same request differently, because of the prompt cache and the order of additions.

File and folder names, and part of the outputs, are in French because the original article is. Useful names: `rejouer.sh` = replay script, `banc/` = bench, `sorties/` = outputs, `candidats.py` = candidates, `essais.py` = runs, `repete.py` = repeat, `flottants.py` = floats, `divergence.py` = divergence, `trace.py` = trace, `tout.sh` = run everything. The files without `.en` in `banc/sorties/` are the French outputs.

## How to replay

- Ollama 0.20.7 (release of 2026-04-13, archive `ollama-darwin.tgz` from https://github.com/ollama/ollama/releases/tag/v0.20.7), with the `phi4` model (14.7 B, Q4_K_M, published in December 2024): `ollama pull phi4`. The model is not in this repo.
- Server settings used: `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`, `OLLAMA_DEBUG=1` (the debug log gives the prompt tokens reused from the cache, which this version does not return in the API answer), everything else at the defaults of this version (one compute slot, context 16384).
- Python 3.14 and NumPy 2.4.0 (only `flottants.py` uses NumPy).
- Ollama must answer on `localhost:11434`, or on the URL given in `OLLAMA_URL` (the outputs here were produced with a separate server on `127.0.0.1:11500`). Set `OLLAMA_LOG` to the server log file to get step 12.
- Durations depend on the machine (measured on an Apple M4 Max, 64 GB). The exact answers can differ on another machine or another Ollama version.

Single command:

```bash
bash rejouer.sh
```

It runs `ollama pull phi4` then `banc/tout.sh`, which rewrites `banc/sorties/`. No third-party data is downloaded.

## File to slide

| File | Slide |
|---|---|
| `banc/candidats.py` → `banc/sorties/01-candidats.txt` | 3 |
| `banc/temperature.py` → `banc/sorties/02-temperature.txt` | 4 |
| `banc/essais.py` → `banc/sorties/03-t08.txt` | 5 |
| `banc/essais.py` → `banc/sorties/04-t0-seed.txt`, `04b-t08-seed.txt`, `06-long-serie.txt` | 6 |
| `banc/essais.py` → `banc/sorties/07-long-parallele.txt` | 7 |
| `banc/trace.py` → `banc/sorties/08-trace-serie.txt`, `09-trace-parallele.txt` (column `cached` at `-`: not returned by this Ollama version) | 7 |
| `banc/sorties/llama-server-args.txt` (runner started by Ollama and its settings, from the server log; this version starts its own `ollama runner`, not `llama-server`) | 7 |
| `banc/cache_log.py` → `banc/sorties/12-cache.txt` (prompt tokens reused from the cache, per step, from the server log) | 7, 8 |
| `banc/repete.py` → `banc/sorties/10-repete.txt` | 8 |
| `banc/divergence.py` → `banc/sorties/11-divergence.txt` | 8 |
| `banc/flottants.py` → `banc/sorties/05-flottants.txt` | 9 |

The `*.en.txt` files are the same measurement redisplayed in English (`--lang en --depuis <json>`), without calling the model again. `banc/log2json.py` rebuilds a JSON from a text output (not needed for the current outputs: all were saved with `--sortie`). `banc/sorties/tout.log` and `trace.log` are the raw logs of one run.

## Third-party data

None. The prompts are written in the scripts. The deck also cites the Thinking Machines article (https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/), not replayed here, and the Ollama docs (https://docs.ollama.com/api/generate).
