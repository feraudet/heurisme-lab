"""Reads the parallel corpus: gettext .po files of the French translation of the Python docs.

Each entry pairs an English paragraph (msgid) with its official French translation (msgstr).
Kept: translated entries, not marked fuzzy, plain prose (no reST markup), at least 8 English words.
Standard library only.
"""
import re
from pathlib import Path

ICI = Path(__file__).resolve().parent
PO = ICI / "telechargements" / "python-docs-fr"
FICHIERS = ["tutorial/errors.po", "tutorial/introduction.po", "library/logging.po",
            "howto/logging.po", "library/subprocess.po", "glossary.po"]

MOT = re.compile(r"\w+")


def mots(texte):
    """Words = runs of letters or digits (l'erreur = 2 words, don't = 2 words), same rule for both languages."""
    return len(MOT.findall(texte))


def _chaine(lignes):
    s = "".join(re.match(r'^(?:msgid|msgstr)?\s*"(.*)"\s*$', l).group(1) for l in lignes)
    return re.sub(r'\\(.)', lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), s)


def entrees(chemin):
    """Yields (msgid, msgstr, fuzzy) for each entry of a .po file."""
    blocs = Path(chemin).read_text(encoding="utf-8").split("\n\n")
    for b in blocs:
        lignes = b.strip().split("\n")
        fuzzy = any(l.startswith("#,") and "fuzzy" in l for l in lignes)
        cle, parts = None, {"msgid": [], "msgstr": []}
        for l in lignes:
            if l.startswith("#"):
                continue
            if l.startswith("msgid "):
                cle = "msgid"
            elif l.startswith("msgstr "):
                cle = "msgstr"
            elif not l.startswith('"'):
                cle = None
                continue
            if cle:
                parts[cle].append(l)
        if parts["msgid"] and parts["msgstr"]:
            yield _chaine(parts["msgid"]), _chaine(parts["msgstr"]), fuzzy


BALISAGE = re.compile(r"::|^\.\. |\|")
ROLE = re.compile(r":[\w:-]+:`~?!?([^`<]*?)(?:\s*<[^>`]*>)?`")


def nettoie(t):
    """Removes reST markup, the same way in both languages: :func:`name` -> name, ``code`` -> code, *word* -> word."""
    t = ROLE.sub(r"\1", t)
    t = re.sub(r"`([^`<]*?)(?:\s*<[^>`]*>)?`_*", r"\1", t)
    t = t.replace("``", "").replace("`", "").replace("**", "")
    t = re.sub(r"(?<!\w)\*(\S[^*]*?)\*(?!\w)", r"\1", t)
    return t.replace("\\ ", "").replace("\\", "")


def paires():
    """Kept (english, french) pairs, in file order."""
    res = []
    for f in FICHIERS:
        for en, fr, fuzzy in entrees(PO / f):
            if not en or not fr or fuzzy:
                continue
            if BALISAGE.search(en) or BALISAGE.search(fr):
                continue
            en, fr = nettoie(en), nettoie(fr)
            if mots(en) < 8:
                continue
            res.append((f, en, fr))
    return res
