"""Summarizes the raw verdicts of verdicts/*.jsonl.

  python3 analyse.py ordre      : position bias (disagreements between the two orders)
  python3 analyse.py longueur   : who wins on the 20 "padding" pairs, verdict by verdict
  python3 analyse.py parades    : each protocol, before and after the "two orders, agreement only" rule
  python3 analyse.py notes      : scoring of a single answer (1 to 10)
Add --lang en for the English display (same numbers, same parsed verdicts).
"""
import json
import sys
from collections import Counter
from pathlib import Path

ICI = Path(__file__).parent
JUGES = ["qwen", "phi4"]
PAIRWISE = ["naif", "egalite", "grille", "reference"]
EN = "--lang" in sys.argv and sys.argv[sys.argv.index("--lang") + 1] == "en"


def T(fr, en):
    return en if EN else fr


def charge(juge, proto):
    f = ICI / "verdicts" / f"{juge}-{proto}.jsonl"
    return [json.loads(l) for l in f.open()] if f.exists() else None


def par_paire(lignes):
    d = {}
    for l in lignes:
        d.setdefault(l["id"], {"type": l["type"]})[l["ordre"]] = l
    return d


def accord(p):
    """Rule of Zheng et al. (3.4): a win only if both orders give it, otherwise a tie."""
    a, b = p["AB"]["gagnant"], p["BA"]["gagnant"]
    return a if a == b else "egalite"


def ordre():
    print(T("Paires jugées dans les deux ordres : le verdict change-t-il quand on inverse A et B ?",
            "Pairs judged in both orders: does the verdict change when A and B are swapped?"))
    print(T(f"{'juge':5s} {'protocole':10s} {'désaccords':>11s} {'dont 1re place':>15s} {'dont 2e place':>14s}",
            f"{'judge':5s} {'protocol':10s} {'disagree':>11s} {'1st place':>15s} {'2nd place':>14s}"))
    for j in JUGES:
        for pr in PAIRWISE:
            L = charge(j, pr)
            if not L:
                continue
            P = par_paire(L)
            n = premier = second = 0
            for p in P.values():
                if p["AB"]["gagnant"] != p["BA"]["gagnant"]:
                    n += 1
                    v = (p["AB"]["verdict"], p["BA"]["verdict"])
                    if v == ("A", "A"):
                        premier += 1
                    elif v == ("B", "B"):
                        second += 1
            print(f"{j:5s} {pr:10s} {n:>8d}/30 {premier:>15d} {second:>14d}")


def longueur():
    print(T("20 paires : réponse courte contre la même réponse rallongée sans fait nouveau.",
            "20 pairs: short answer against the same answer padded with no new fact."))
    print(T("Chaque paire jugée deux fois (A/B puis B/A), soit 40 verdicts par ligne.",
            "Each pair judged twice (A/B then B/A), so 40 verdicts per row."))
    print(T(f"{'juge':5s} {'protocole':10s} {'courte':>7s} {'rallongée':>10s} {'égalité':>8s}",
            f"{'judge':5s} {'protocol':10s} {'short':>7s} {'padded':>10s} {'tie':>8s}"))
    for j in JUGES:
        for pr in PAIRWISE:
            L = charge(j, pr)
            if not L:
                continue
            c = Counter(l["gagnant"] for l in L if l["type"] == "longueur")
            print(f"{j:5s} {pr:10s} {c['bonne']:>7d} {c['autre']:>10d} {c['egalite']:>8d}"
                  + (T(f"   illisible : {c['?']}", f"   unreadable: {c['?']}") if c["?"] else ""))


def parades():
    print(T("Remplissage : 20 paires, la rallongée ne devrait jamais gagner.",
            "Padding: 20 pairs, the padded answer should never win."))
    print(T("Fausses : 10 paires (5 de même longueur, 5 fausses et rallongées), la bonne doit gagner.",
            "Wrong: 10 pairs (5 same length, 5 wrong and padded), the correct one must win."))
    print(T("« brut » : 40 et 20 verdicts. « accord » : 20 et 10 paires, une victoire seulement si les deux ordres la donnent.",
            "\"raw\": 40 and 20 verdicts. \"agree\": 20 and 10 pairs, a win only when both orders give it."))
    print(T(f"{'juge':5s} {'protocole':10s} | {'rallongée gagne':>15s} {'accord':>7s} | {'bonne gagne (fausses)':>21s} {'accord':>7s}",
            f"{'judge':5s} {'protocol':10s} | {'padded wins':>15s} {'agree':>7s} | {'correct wins (wrong)':>21s} {'agree':>7s}"))
    for j in JUGES:
        for pr in PAIRWISE:
            L = charge(j, pr)
            if not L:
                continue
            P = par_paire(L)
            lg = [l for l in L if l["type"] == "longueur"]
            fx = [l for l in L if l["type"] != "longueur"]
            r_brut = sum(l["gagnant"] == "autre" for l in lg)
            b_brut = sum(l["gagnant"] == "bonne" for l in fx)
            r_acc = sum(accord(p) == "autre" for p in P.values() if p["type"] == "longueur")
            b_acc = sum(accord(p) == "bonne" for p in P.values() if p["type"] != "longueur")
            print(f"{j:5s} {pr:10s} | {r_brut:>12d}/40 {r_acc:>4d}/20 | {b_brut:>18d}/20 {b_acc:>4d}/10")


def notes():
    print(T("Chaque réponse notée seule, de 1 à 10 : pas de paire, donc pas d'ordre.",
            "Each answer scored alone, 1 to 10: no pair, so no order."))
    print(T(f"{'juge':5s} {'paires':14s} {'moy. bonne':>10s} {'moy. autre':>10s} {'bonne > autre':>14s} {'=':>3s} {'autre > bonne':>14s}",
            f"{'judge':5s} {'pairs':14s} {'avg good':>10s} {'avg other':>10s} {'good > other':>14s} {'=':>3s} {'other > good':>14s}"))
    for j in JUGES:
        L = charge(j, "note")
        if not L:
            continue
        d = {}
        for l in L:
            d.setdefault(l["id"], {"type": l["type"]})[l["reponse"]] = l["note"]
        # a "score" outside 1..10 is not a score: the pair is dropped and counted separately
        hors = [i for i, v in d.items() if not all(isinstance(v[q], int) and 1 <= v[q] <= 10 for q in ("bonne", "autre"))]
        for t, nom in (("longueur", T("remplissage", "padding")), ("fausse", T("fausses", "wrong"))):
            S = [v for i, v in d.items() if v["type"].startswith(t) and i not in hors]
            mb = sum(v["bonne"] for v in S) / len(S)
            ma = sum(v["autre"] for v in S) / len(S)
            sup = sum(v["bonne"] > v["autre"] for v in S)
            eg = sum(v["bonne"] == v["autre"] for v in S)
            inf = sum(v["bonne"] < v["autre"] for v in S)
            print(f"{j:5s} {nom:14s} {mb:>10.2f} {ma:>10.2f} {sup:>14d} {eg:>3d} {inf:>14d}")
        for i in hors:
            v = d[i]
            print(T(f"{j:5s} paire {i} écartée, note hors de 1 à 10 : bonne={v['bonne']} autre={v['autre']}",
                    f"{j:5s} pair {i} left out, score outside 1 to 10: good={v['bonne']} other={v['autre']}"))


if __name__ == "__main__":
    {"ordre": ordre, "longueur": longueur, "parades": parades, "notes": notes}[sys.argv[1]]()
