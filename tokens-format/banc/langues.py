"""The same text (an agent instruction) in French and in English: how many tokens?

Usage: python banc/langues.py
"""
from langue import t as tr
from tok import NOMS, compte, morceaux

FR = """Tu es un agent d'exploitation. Avant chaque redémarrage, vérifie que le serveur n'héberge aucune base de données primaire et que la réplication est à jour. Si une opération échoue, ne réessaie pas plus de deux fois : arrête-toi, résume l'erreur en une phrase et demande une validation humaine. Réponds toujours en français, avec des phrases courtes."""

EN = """You are an operations agent. Before each restart, check that the server hosts no primary database and that replication is up to date. If an operation fails, do not retry more than twice: stop, summarize the error in one sentence and ask for human approval. Always answer in English, with short sentences."""

print(f"{tr('texte', 'text'):<10}{tr('caractères', 'characters'):>11}{tr('mots', 'words'):>6}" + "".join(f"{n:>13}" for n in NOMS))
r = {}
for nom, t in ((tr("français", "french"), FR), (tr("anglais", "english"), EN)):
    c = compte(t)
    r[nom] = c
    print(f"{nom:<10}{len(t):>11}{len(t.split()):>6}" + "".join(f"{c[n]:>13}" for n in NOMS))
print(f"{'fr / en':<27}" + "".join(f"{r[tr('français', 'french')][n] / r[tr('anglais', 'english')][n]:>12.2f}x" for n in NOMS))

for phrase in ("vérifie que la réplication est à jour", "check that replication is up to date"):
    print()
    for n in ("o200k_base", "cl100k_base"):
        m = morceaux(phrase, n)
        print(f"{n:<12} {len(m):>2} : " + "·".join(x.replace(" ", "␣") for x in m))
