"""Ratio of each format to the CSV, for each tokenizer.

Fourth column: the phi4 tokenizer, read from Ollama's prompt_eval_count (largest value
for each format in data/qualite.jsonl, full prompt: instruction + data + question).
Usage: python banc/ratios.py
"""
import json
from pathlib import Path

from langue import f as fmt

DATA = Path(__file__).resolve().parent.parent / "data"
c = json.loads((DATA / "comptes.json").read_text())
q = [json.loads(x) for x in (DATA / "qualite.jsonl").read_text().splitlines()]
phi = {f: max(x["prompt_eval_count"] for x in q if x["format"] == f) for f in c}
cols = ["o200k_base", "cl100k_base", "qwen2.5"]
print(f"{'format':<13}" + "".join(f"{n:>13}" for n in cols) + f"{'phi4 (ollama)':>15}")
for f in c:
    print(f"{fmt(f):<13}" + "".join(f"{c[f][n] / c['csv'][n]:>12.2f}x" for n in cols) + f"{phi[f] / phi['csv']:>14.2f}x")
