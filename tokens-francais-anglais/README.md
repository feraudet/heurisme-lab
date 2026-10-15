# tokens-francais-anglais

This bench goes with the deck https://heurisme.fr/en/blog/tokens-francais-anglais/ : the same text costs more tokens in French than in English. It counts the tokens of a parallel French / English corpus with six public tokenizers, measures what the accents weigh, splits one sentence word by word, and follows one example: a system prompt and an internal runbook sent to an LLM with every question.

It follows the bench of [JSON, YAML or CSV: what a prompt costs](../tokens-format/) (same tokenizer library versions).

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `calcule.sh` = compute (runs in the container), `tok.py` = the tokenizers, `po.py` = reads the corpus, `corpus.py` = counts the corpus, `accents.py` = accents, `decoupe.py` = split, `exemple.py` = the example, `exemple/` = the example files (`prompt-systeme` = system prompt, `doc-interne` = internal doc), `telechargements/` = downloads, `sorties/` = outputs. The outputs themselves are in English.

## How to replay

- Docker, for the `python:3.12-slim-bookworm` container in arm64 (pinned by digest in `rejouer.sh`). On x86_64, remove `--platform linux/arm64` in `rejouer.sh`.
- `curl` and `shasum` on the host, to download the third-party files and check their sha256.
- In the container, pip installs exact versions with `--no-deps` (see `requirements.txt`): tiktoken 0.13.0 (2026-05-15), tokenizers 0.23.1 (2026-04-27), regex 2026.9.29 (2026-09-29). See `sorties/00-versions.txt`.

Single command:

```bash
bash rejouer.sh
```

It downloads the files listed below into `telechargements/` (sha256 checked, not in the repo), then rewrites `sorties/01-corpus.txt` to `sorties/04-exemple.txt`. Compare with the files provided: they come out byte for byte. Nothing is random and nothing is timed: two runs give the same outputs.

No model is called and no API key is needed: the bench only counts tokens.

## The tokenizers

| Name in the outputs | Source | Pinned at |
|---|---|---|
| `cl100k_base` (GPT-4) | https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken | sha256 `223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7` |
| `o200k_base` (GPT-4o) | https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken | sha256 `446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d` |
| `Mistral-7B-v0.3` | `tokenizer.json` of https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3 (Apache 2.0) | revision `c170c708c41dac9275d15a8fff4eca08d52bab71`, sha256 `e553af6fff7d7ad76e830608b218c5c0b0822998d5a1a96099a74cd3c1cb1a49` |
| `Mistral-NeMo` (Tekken) | `tokenizer.json` of https://huggingface.co/mistralai/Mistral-Nemo-Instruct-2407 (Apache 2.0) | revision `04d8a90549d23fc6bd7f642064003592df51e9b3`, sha256 `e11c71726323d33da7b8d6f6f269f1988931c0a52b7122bcdd8c05042974e0db` |
| `Qwen2.5` | `tokenizer.json` of https://huggingface.co/Qwen/Qwen2.5-7B-Instruct (Apache 2.0) | revision `a09a35458c702b33eeacc393d103063234e8bc28`, sha256 `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |
| `CroissantLLM` | `tokenizer.json` of https://huggingface.co/croissantllm/CroissantLLMBase (MIT) | revision `47baabdf7ed66de1d33e159e62a5aa947c7e2553`, sha256 `b028de04ca166adca7f1394d44599732c437387b21cc14ba236ac1f56198cf7f` |

Tokens are counted without special tokens (no beginning-of-sequence token). Claude's tokenizer is not measured: Anthropic only exposes it through the `count_tokens` API, which needs a key.

## The corpus

The French translation of the Python documentation (https://github.com/python/python-docs-fr, published at https://docs.python.org/fr/), commit `dda0482a5960c8ede02857231a94aa8c61be35e8` of branch 3.13. Each gettext `.po` entry pairs an English paragraph (`msgid`) with its official French translation (`msgstr`). Six files are used:

| File | sha256 |
|---|---|
| `tutorial/errors.po` | `195f3dd167f9fe4385d0a87b72b4e76b3b0187f644dd0fa13ee6d648ce48811e` |
| `tutorial/introduction.po` | `7ed4ee67e5afe499a6da1b3271aa605c03f539e680187b9ab7a658e9d0a6ee29` |
| `library/logging.po` | `28ce850d21c67676855245aad4b71029333d504e7534460c2536a91aa668043c` |
| `howto/logging.po` | `e662e514644091dcb4b90ac7d5e8d148d4ad6a9c2d1b52c7056af177d0dc9d1e` |
| `library/subprocess.po` | `16ec1d4ff2ddc98315519c701d477ffa2dcadbea640341e63613c62a55cd9b0b` |
| `glossary.po` | `a2abdd10d9be2aaafdb9c152cc67fbb86b3979816aaa290c45451df21b445bbf` |

`po.py` keeps the entries that are translated and not marked fuzzy, drops tables, directives and literal blocks, removes the reST markup the same way in both languages (`:func:` roles, backquotes, asterisks), and keeps the pairs with at least 8 English words: 523 pairs. Words are counted the same way in both languages, as runs of letters or digits (`l'erreur` and `don't` are two words each).

License: the translations are contributed to the PSF under CC0 (see the README of python-docs-fr); the English text is the Python documentation, under the PSF license. Neither is copied here.

## The example

`exemple/prompt-systeme.fr.md` and `exemple/doc-interne.fr.md` were written for the article (an on-call assistant and a runbook to restart a node of a PostgreSQL cluster), and `*.en.md` are their English translations. They are released with the scripts under the MIT license.

## File to slide

| File | Slide |
|---|---|
| `exemple/*.md`, `sorties/04-exemple.txt` lines 3-4 | 2 (the example) |
| `sorties/03-decoupe.txt` | 3 (the word "redémarre" in bytes and tokens), 4 (one rule split word by word) |
| `sorties/01-corpus.txt` | 3 (vocabulary size), 5 (FR/EN ratio per tokenizer), 6 (tokens per word), 8 (content per window) |
| `sorties/02-accents.txt` | 7 (without accents, decomposed accents) |
| `sorties/04-exemple.txt` | 8 (tokens per question, 10,000 questions) |
| `sorties/00-versions.txt` | versions of Python and of the packages in the container |

## Third-party data

None is copied here: only the addresses and sha256 above. `rejouer.sh` downloads them into `telechargements/`, which is ignored by git.
