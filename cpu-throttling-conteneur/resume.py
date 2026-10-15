#!/usr/bin/env python3
"""Summaries of the raw files in brut/ (written by rejouer.sh), one section per output file.

usage: python3 resume.py cgroup|latency|cpustat|job
"""
import os
import statistics
import sys

BRUT = "brut"
RUNS = int(os.environ.get("RUNS", "5"))
CONFIGS = [
    ("no-limit", "docker run"),
    ("cpus-1", "docker run --cpus=1"),
    ("cpuset-0", "docker run --cpuset-cpus=0"),
    ("cpus-4", "docker run --cpus=4"),
]


def lire(cfg, run, quoi):
    with open(os.path.join(BRUT, f"{cfg}-{run}-{quoi}.txt")) as f:
        return f.read().split("\n")


def centile(valeurs, p):
    v = sorted(valeurs)
    return v[min(len(v) - 1, int(p * len(v)))]


def latences(cfg, run):
    return [int(x) / 1000 for x in lire(cfg, run, "latency") if x]


def stat(cfg, run):
    """cpu.stat deltas over the measure, plus its duration in seconds."""
    avant, apres = lire(cfg, run, "stat-before"), lire(cfg, run, "stat-after")
    duree = float(apres[0]) - float(avant[0])
    d = {}
    for a, b in zip(avant[1:], apres[1:]):
        if a:
            cle, x = a.split()
            d[cle] = int(b.split()[1]) - int(x)
    return d, duree


def jobs(cfg, run):
    return [l.split() for l in lire(cfg, run, "jobs") if l.startswith("job ")]


def cgroup():
    print("what the container sees in its cgroup (first run of each config)")
    print()
    print(f"{'command':<28} {'cpu.max':<15} cpuset.cpus.effective")
    for cfg, cmd in CONFIGS:
        m = lire(cfg, 1, "cpumax")
        print(f"{cmd:<28} {m[0]:<15} {m[1]}")


def latency():
    print(f"{RUNS} runs per config; per run: 1000 requests, one every 20 ms, 1 ms of CPU each")
    print("background job in the same container: 4 threads x 50 ms of CPU, every second")
    print("latency in ms, counted from the time each request was due")
    print()
    print("p99: median of the runs [lowest-highest]")
    for cfg, cmd in CONFIGS:
        p99 = [centile(latences(cfg, r), 0.99) for r in range(1, RUNS + 1)]
        cpu = [stat(cfg, r)[0]["usage_usec"] / 1e6 / stat(cfg, r)[1] for r in range(1, RUNS + 1)]
        print(f"{cmd:<28} p99 {statistics.median(p99):6.1f} [{min(p99):.1f}-{max(p99):.1f}]"
              f"   average CPU {statistics.median(cpu):.2f}")
    print()
    print(f"{'config':<10} {'run':>3} {'p50':>6} {'p90':>6} {'p99':>6} {'max':>6}")
    for cfg, _ in CONFIGS:
        for r in range(1, RUNS + 1):
            v = latences(cfg, r)
            print(f"{cfg:<10} {r:>3} {centile(v, .5):6.1f} {centile(v, .9):6.1f} {centile(v, .99):6.1f} {max(v):6.1f}")


def cpustat():
    print("cpu.stat of the container: what changed during the measure (first run of each config)")
    print()
    cles = ["usage_usec", "nr_periods", "nr_throttled", "throttled_usec"]
    print(f"{'config':<10} {'seconds':>7} " + " ".join(f"{c:>14}" for c in cles))
    for cfg, _ in CONFIGS:
        d, duree = stat(cfg, 1)
        print(f"{cfg:<10} {duree:7.1f} " + " ".join(f"{d[c]:>14}" for c in cles))
    print()
    print("nr_throttled / nr_periods, median of the runs [lowest-highest]")
    for cfg, _ in CONFIGS:
        r = []
        for run in range(1, RUNS + 1):
            d, _ = stat(cfg, run)
            r.append(d["nr_throttled"] / d["nr_periods"] if d["nr_periods"] else 0.0)
        print(f"{cfg:<10} {statistics.median(r):5.1%} [{min(r):.1%}-{max(r):.1%}]")


def job():
    print("background job: 4 threads x 50 ms of CPU = 200 ms of CPU")
    print("wall time of the job in ms, median of all jobs of all runs [lowest-highest]")
    for cfg, _ in CONFIGS:
        w = [float(j[3]) for r in range(1, RUNS + 1) for j in jobs(cfg, r)]
        print(f"{cfg:<10} {statistics.median(w):6.1f} [{min(w):.1f}-{max(w):.1f}]  ({len(w)} jobs)")
    print()
    print("job 10 of the first run, as printed by api (pause = no job thread progressed for more than 2 ms)")
    for cfg, _ in CONFIGS:
        j = jobs(cfg, 1)[9]
        print(f"{cfg:<10} " + " ".join(j))


if __name__ == "__main__":
    {"cgroup": cgroup, "latency": latency, "cpustat": cpustat, "job": job}[sys.argv[1]]()
