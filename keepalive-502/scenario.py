#!/usr/bin/env python3
"""Runs one scenario of the bench several times and prints what it saw.

usage: python3 scenario.py <Node.js keepAliveTimeout ms|default> <nginx upstream keepalive_timeout> <GET|POST> <runs>

Each run starts Node.js and nginx afresh, plays the client on 20 lanes, then stops both and
reads the nginx logs. The error log lines are printed without their date, process id,
connection number and port, which change on every run; the message itself is copied as is.
"""
import os
import re
import statistics
import subprocess
import sys
import time
from collections import Counter

LANES = 20
GAPS = [3000] + list(range(4980, 5021, 2)) + [7000]
RUN = "/w/run"

backend_timeout, nginx_timeout, method, runs = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])


def one_run():
    os.makedirs(RUN, exist_ok=True)
    for f in ("error.log", "access.log"):
        open(os.path.join(RUN, f), "w").close()
    with open(os.path.join(RUN, "nginx.conf"), "w") as f:
        subprocess.run(["python3", "nginx_conf.py", nginx_timeout, str(LANES)], stdout=f, check=True)
    node = subprocess.Popen(["node", "backend.js", backend_timeout, "3000", str(LANES)],
                            stdout=subprocess.PIPE, text=True)
    banner = node.stdout.readline().strip()
    subprocess.run(["nginx", "-c", os.path.join(RUN, "nginx.conf")], check=True)
    time.sleep(0.5)
    client = subprocess.run(["python3", "client.py", str(LANES), method] + [str(g) for g in GAPS],
                            capture_output=True, text=True, check=True).stdout
    subprocess.run(["nginx", "-s", "quit", "-c", os.path.join(RUN, "nginx.conf")], check=True)
    time.sleep(1)
    node.terminate()
    node.wait()
    errors = Counter()
    for line in open(os.path.join(RUN, "error.log")):
        m = re.match(r"\S+ \S+ \[(\w+)\] \d+#\d+: \*\d+ (.*?), client: .*?, request: (\"[^\"]*\")", line)
        if m:
            errors[f"[{m.group(1)}] {m.group(2)}, request: {m.group(3)}"] += 1
        else:
            errors["(unparsed) " + line.strip()] += 1
    access = Counter(line.strip() for line in open(os.path.join(RUN, "access.log")))
    return banner, client, errors, access


print(f"$ python3 scenario.py {backend_timeout} {nginx_timeout} {method} {runs}")
print(f"nginx: upstream keepalive_timeout {nginx_timeout}, proxy_http_version 1.1, Connection \"\"")
totals = []
for k in range(1, runs + 1):
    banner, client, errors, access = one_run()
    if k == 1:
        print(banner)
        print()
        print(f"--- run 1, client side ---")
        print(client.rstrip())
    bad = int(client.strip().split("\n")[-1].split()[-1])
    totals.append(bad)
    print()
    print(f"--- run {k}: {bad} x 502 out of {LANES * len(GAPS)} requests ---")
    print("nginx error.log (date, pid, connection and port removed):")
    if not errors:
        print("  (empty)")
    for msg, n in sorted(errors.items()):
        print(f"  {n:3d}  {msg}")
    print("nginx access.log ($request_method $status upstream=$upstream_status):")
    for line, n in sorted(access.items()):
        print(f"  {n:3d}  {line}")
print()
print(f"502 per run: {' '.join(str(t) for t in totals)}")
print(f"median {statistics.median(totals):g}, min {min(totals)}, max {max(totals)}, over {runs} runs of {LANES * len(GAPS)} requests")
