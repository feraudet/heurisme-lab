#!/usr/bin/env python3
"""Turns the raw CSVs into per-agent costs. Writes raw/synthese.txt.

Per-agent cost = slope of RSS between 10,000 agents and the last sample
(so the fixed cost of the process and of the allocator warm-up drops out).
"""
import csv
import pathlib
import sys

RAW = pathlib.Path(__file__).parent / "raw"
GIB, KIB = 1024 ** 3, 1024
PI5 = 8 * GIB  # Raspberry Pi 5, 8 GB model (8 GiB of RAM)


def lire(nom):
    with open(RAW / nom) as f:
        return [{k: int(v) for k, v in r.items()} for r in csv.DictReader(f)]


def pente(rows, cle="rss_bytes", depuis=10_000):
    a = next(r for r in rows if r["agents"] == depuis)
    b = rows[-1]
    return (b[cle] - a[cle]) / (b["agents"] - a["agents"]), b


def ligne(rows, n):
    return next((r for r in rows if r["agents"] == n), None)


out = []
p = out.append
p("== 1. Infinity agent_scale (commit 341f6c2), agents idle between turns, 20 turns each")
inf = lire("infinity_80000x20.csv")
s, last = pente(inf)
p(f"  agents mesurés        {last['agents']}")
p(f"  RSS final             {last['rss_bytes'] / GIB:.2f} GiB ({last['rss_bytes'] / 1e9:.2f} GB)")
p(f"  coût par agent        {s / KIB:.1f} KiB ({s / 1000:.0f} kB), pente 10 000 -> {last['agents']}")
r75 = ligne(inf, 75_000)
p(f"  RSS à 75 000 agents   {r75['rss_bytes'] / GIB:.2f} GiB, Pi 5 = {PI5 / GIB:.0f} GiB, "
  f"reste {(PI5 - r75['rss_bytes']) / GIB:.2f} GiB pour le système")
p(f"  calcul du blog        75 000 x 100 kB = {75_000 * 100e3 / 1e9:.1f} GB = {75_000 * 100e3 / GIB:.2f} GiB")
p(f"  agents dans 8 GiB     {int(PI5 / s)} (pente seule, sans OS)")

p("")
p("== 2. Variante pending : même chose + un dernier appel d'outil qui ne répond jamais")
p("   (run à 50 000 agents : à 80 000, la VM Docker de 16 Go swappe dès 60 000 agents et la RSS")
p("    plafonne, voir raw/pending_80000x20_swap.csv ; ce run-là n'est pas utilisé)")
pen = lire("pending_50000x20.csv")
s2, last2 = pente(pen)
p(f"  agents mesurés        {last2['agents']}, RSS final {last2['rss_bytes'] / GIB:.2f} GiB")
p(f"  coût par agent        {s2 / KIB:.1f} KiB, soit +{(s2 - s) / KIB:.1f} KiB par rapport à idle ({s2 / s:.2f} fois)")
p(f"  75 000 agents, extrapolé sur la pente : {(last2['rss_bytes'] + s2 * (75_000 - last2['agents'])) / GIB:.2f} GiB")
p(f"  agents dans 8 GiB     {int(PI5 / s2)} (pente seule, sans OS)")

p("")
p("== 3. Modèle naïf : historique de même forme, l'agent attend un résultat d'outil")
base = None
for mode in ("none", "task", "thread"):
    rows = lire(f"naive_{mode}_80000x20.csv")
    sm, lm = pente(rows)
    r65 = ligne(rows, 65_000)
    if mode == "none":
        base = r65
    extra = (r65["rss_bytes"] - base["rss_bytes"]) / 65_000
    vm = (r65["vm_bytes"] - base["vm_bytes"]) / 65_000
    p(f"  {mode:6}  dernier échantillon {lm['agents']:>6} agents, {sm / KIB:5.1f} KiB/agent ; "
      f"à 65 000 : +{extra:,.0f} o RSS et +{vm / 2**20:.2f} MiB virtuels par agent vs none, "
      f"{r65['maps']} mappings")
thr = lire("naive_thread_80000x20.csv")
r10 = ligne(thr, 10_000)
p(f"  thread : {r10['maps']} mappings pour 10 000 threads = {(r10['maps'] - 23) / 10_000:.2f} par thread")
lim = (RAW / "limites_noyau.txt").read_text().strip()
p(f"  limites : {lim}")
log = (RAW / "naive_thread_80000x20.log").read_text()
err = next((l for l in log.splitlines() if "failed" in l), "pas d'erreur")
p(f"  arrêt après {thr[-1]['agents']} threads : {err.strip()}")

texte = "\n".join(out) + "\n"
(RAW / "synthese.txt").write_text(texte)
sys.stdout.write(texte)
