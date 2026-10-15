#!/usr/bin/env python3
"""The client: on each lane, one request, a pause, the next request, and so on.

usage: python3 client.py <lanes> <GET|POST> <gap ms> [<gap ms> ...]

The pause (the gap) is measured from the end of the previous response to the next request.
Every lane plays the same list of gaps, in the same order. Prints, for each gap, how many
requests came back 502, then the total.
"""
import http.client
import sys
import threading
import time

lanes, method = int(sys.argv[1]), sys.argv[2]
gaps = [int(x) for x in sys.argv[3:]]

results = {}  # (lane, gap) -> status
lock = threading.Lock()


def send(port):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    body = b'{"order": 42}' if method == "POST" else None
    conn.request(method, "/orders", body=body, headers={"Connection": "close"})
    status = conn.getresponse().status
    conn.close()
    return status


def lane(n):
    port = 8000 + n
    send(port)  # opens the idle connection between nginx and Node.js
    for gap in gaps:
        time.sleep(gap / 1000)
        status = send(port)
        with lock:
            results[(n, gap)] = status


threads = [threading.Thread(target=lane, args=(n,)) for n in range(lanes)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"{method}, {lanes} lanes, {len(gaps)} gaps, {lanes * len(gaps)} requests")
print("gap (ms)  requests  502")
total = bad = 0
for gap in gaps:
    statuses = [results[(n, gap)] for n in range(lanes)]
    n502 = statuses.count(502)
    others = sorted(set(s for s in statuses if s not in (200, 502)))
    total += len(statuses)
    bad += n502
    extra = f"  other: {others}" if others else ""
    print(f"{gap:8d}  {len(statuses):8d}  {n502:3d}{extra}")
print(f"total     {total:8d}  {bad:3d}")
