"""The six tokenizers of the bench, all offline once rejouer.sh has downloaded their files."""
import os
from pathlib import Path

ICI = Path(__file__).resolve().parent
TEL = ICI / "telechargements"
os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(TEL / "tiktoken"))

import tiktoken  # noqa: E402
from tokenizers import Tokenizer  # noqa: E402

# display name -> loader
_TIK = {"cl100k_base": "cl100k_base", "o200k_base": "o200k_base"}
_HF = {"Mistral-7B-v0.3": "mistral-7b-v0.3.json", "Mistral-NeMo": "mistral-nemo.json",
       "Qwen2.5": "qwen2.5.json", "CroissantLLM": "croissantllm.json"}
NOMS = list(_TIK) + list(_HF)

_enc = {n: tiktoken.get_encoding(e) for n, e in _TIK.items()}
_enc.update({n: Tokenizer.from_file(str(TEL / f)) for n, f in _HF.items()})


def taille(nom):
    """Vocabulary size."""
    e = _enc[nom]
    return e.n_vocab if nom in _TIK else e.get_vocab_size(with_added_tokens=True)


def compte(nom, texte):
    e = _enc[nom]
    if nom in _TIK:
        return len(e.encode(texte, disallowed_special=()))
    return len(e.encode(texte, add_special_tokens=False).ids)


def morceaux(nom, texte):
    """The text, split into tokens. A token that holds only part of a UTF-8 character is shown as its bytes."""
    e = _enc[nom]
    if nom in _TIK:
        res = []
        for t in e.encode(texte, disallowed_special=()):
            b = e.decode_single_token_bytes(t)
            try:
                res.append(b.decode("utf-8"))
            except UnicodeDecodeError:
                res.append("<" + " ".join(f"{x:02X}" for x in b) + ">")
        return res
    enc = e.encode(texte, add_special_tokens=False)
    res = []
    for (a, b), tok in zip(enc.offsets, enc.tokens):
        if tok.startswith("<0x") and tok.endswith(">"):  # byte fallback (SentencePiece)
            res.append("<" + tok[3:-1] + ">")
        else:
            res.append(texte[a:b])
    return res
