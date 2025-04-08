"""Relay between two pty pairs (socat): logs each packet of bytes with its timestamp.

Usage: python tap.py A B [--gap-after N --gap-ms MS]
  A: client side (master), B: server side (slave).
  --gap-after N: in the master -> slave direction, cuts each frame after N bytes
  and waits MS milliseconds before sending the rest (simulates a USB latency timer).
"""
import argparse
import os
import select
import sys
import time

p = argparse.ArgumentParser()
p.add_argument("a")
p.add_argument("b")
p.add_argument("--gap-after", type=int, default=0)
p.add_argument("--gap-ms", type=float, default=0)
args = p.parse_args()

fa = os.open(args.a, os.O_RDWR | os.O_NOCTTY)
fb = os.open(args.b, os.O_RDWR | os.O_NOCTTY)
t0 = None


def log(sens, data):
    global t0
    now = time.monotonic()
    if t0 is None:
        t0 = now
    print(f"{(now - t0) * 1000:9.3f} ms  {sens}  {data.hex(' ')}", flush=True)


while True:
    r, _, _ = select.select([fa, fb], [], [])
    for fd in r:
        data = os.read(fd, 512)
        if fd == fa:
            if args.gap_after and len(data) > args.gap_after:
                part1, part2 = data[: args.gap_after], data[args.gap_after :]
                log("maître  -> esclave", part1)
                os.write(fb, part1)
                time.sleep(args.gap_ms / 1000)
                log("maître  -> esclave", part2)
                os.write(fb, part2)
            else:
                log("maître  -> esclave", data)
                os.write(fb, data)
        else:
            log("esclave -> maître ", data)
            os.write(fa, data)
