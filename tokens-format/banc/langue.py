"""Output language: --lang fr (default) or --lang en on the command line."""
import sys

EN = "--lang" in sys.argv and sys.argv[sys.argv.index("--lang") + 1] == "en"
ARGS = [a for k, a in enumerate(sys.argv[1:], 1) if a != "--lang" and sys.argv[k - 1] != "--lang"]

FORMATS_EN = {"json-indente": "json-indented", "json-minifie": "json-minified"}


def f(nom):
    """Displayed format name."""
    return FORMATS_EN.get(nom, nom) if EN else nom


def t(fr, en):
    return en if EN else fr
