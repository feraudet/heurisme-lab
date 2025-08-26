#!/usr/bin/env python3
"""Reads the output of "sigrok-cli -A uart=rx-data:rx-warnings" (hex format) and counts
the decoded bytes, the correct ones (compared with a repeated "Hello World!\r\n") and the framing errors."""
import sys
attendu = b"Hello World!\r\n"
octets, fe = [], 0
for l in sys.stdin:
    v = l.split(": ", 1)[1].strip()
    if v == "Frame error":
        fe += 1
    elif len(v) == 2:
        octets.append(int(v, 16))
justes = sum(1 for i, o in enumerate(octets) if o == attendu[i % len(attendu)])
if "--en" in sys.argv:  # English output for en.html
    print("%s %3d bytes  %3d correct  %3d framing errors" % (sys.argv[1], len(octets), justes, fe))
else:
    print("%s %3d octets  %3d justes  %3d framing errors" % (sys.argv[1], len(octets), justes, fe))
