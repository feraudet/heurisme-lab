"""The three tokenizers of the bench, all offline once the files are cached."""
import os
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(ICI / "telechargements" / "tiktoken"))

import tiktoken  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402

QWEN = ICI / "telechargements" / "qwen2.5-tokenizer.json"  # downloaded by rejouer.sh

_o200k = tiktoken.get_encoding("o200k_base")
_cl100k = tiktoken.get_encoding("cl100k_base")
_qwen = Tokenizer.from_file(str(QWEN))

NOMS = ["o200k_base", "cl100k_base", "qwen2.5"]


def compte(texte):
    return {
        "o200k_base": len(_o200k.encode(texte)),
        "cl100k_base": len(_cl100k.encode(texte)),
        "qwen2.5": len(_qwen.encode(texte, add_special_tokens=False).ids),
    }


def morceaux(texte, nom="o200k_base"):
    """Splits into tokens, returns the list of text pieces."""
    if nom == "qwen2.5":
        enc = _qwen.encode(texte, add_special_tokens=False)
        return [texte[a:b] for a, b in enc.offsets]
    e = _o200k if nom == "o200k_base" else _cl100k
    return [e.decode_single_token_bytes(t).decode("utf-8", "replace") for t in e.encode(texte)]
