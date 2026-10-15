#!/usr/bin/env python3
"""Filters the output of openssl s_client: hides what changes at each replay, keeps the rest as is.

- the base64 body of each certificate (new keys at each replay): one line "(base64 masked)";
- the TLS session: identifiers, keys, tickets, start time and byte counts are replaced by "(masked)".
Everything else is copied unchanged, in order.
"""
import re
import sys

dans_pem = False
for ligne in sys.stdin:
    ligne = ligne.rstrip("\n")
    if ligne.startswith("-----BEGIN"):
        print(ligne); print("(base64 masked: new keys at each replay)"); dans_pem = True; continue
    if ligne.startswith("-----END"):
        print(ligne); dans_pem = False; continue
    if dans_pem:
        continue
    ligne = re.sub(r"has read \d+ bytes and written \d+ bytes", "has read (masked) bytes and written (masked) bytes", ligne)
    ligne = re.sub(r"^(\s*(Session-ID|Session-ID-ctx|Resumption PSK|Master-Key|Start Time|TLS session ticket lifetime hint)\s*:).*", r"\1 (masked)", ligne)
    if re.match(r"^\s*[0-9a-f]{4} - ", ligne):
        continue  # hex dump of the session ticket
    print(ligne)
