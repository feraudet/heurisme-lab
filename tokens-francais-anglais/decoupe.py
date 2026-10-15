"""One rule of the system prompt, split into tokens word by word, in French and in English.

Inside a word, tokens are separated by « · ». A leading space is shown as « ␣ ».
A token that holds only part of a UTF-8 character is shown as its bytes, like <C3>.
Usage: python3 decoupe.py [tokenizer ...]
"""
import re
import sys

from tok import NOMS, morceaux

PHRASES = {
    "french": "Ne propose jamais une commande qui redémarre un nœud de base de données.",
    "english": "Never suggest a command that restarts a database node.",
}


def par_mot(nom, texte):
    """Groups the tokens by word: a token goes to the word where its first visible character is."""
    mots = [[m.group(), m.start(), m.end(), []] for m in re.finditer(r"\S+", texte)]
    pos = 0
    for m in morceaux(nom, texte):
        if m.startswith("<") and m.endswith(">") and len(m) > 2:  # partial character: no visible text of its own
            n = 0
            debut = pos
        else:
            n = len(m)
            debut = pos + (len(m) - len(m.lstrip(" ")))
        for w in mots:
            if w[1] <= debut < w[2] or (n == 0 and w[1] <= pos <= w[2]):
                w[3].append(m)
                break
        pos += n
    return mots


noms = sys.argv[1:] or ["o200k_base", "Mistral-7B-v0.3", "CroissantLLM"]
for nom in noms:
    assert nom in NOMS, nom
    for langue, texte in PHRASES.items():
        mots = par_mot(nom, texte)
        total = sum(len(w[3]) for w in mots)
        print(f"{nom}, {langue}: {total} tokens for {len(mots)} words")
        for mot, _, _, ms in mots:
            print(f"  {mot:<11}{len(ms):>2}  " + "·".join(x.replace(" ", "␣") for x in ms))
        print()
