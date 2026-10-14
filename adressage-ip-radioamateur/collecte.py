#!/usr/bin/env python3
"""Downloads the public data of the bench into raw/ (no account, no key).

- ARIN RDAP for 44.0.0.0/8, 44.192.0.0/10, 44.0.0.0/9 and 44.151.0.0/16, and the ARDC entity;
- the AMPRNet geofeed published by ARDC (URL found in the RDAP remark);
- RIPEstat routing-status for 44.0.0.0/8 at a fixed RIS dump (2026-10-14 16:00 UTC),
  split in halves wherever the 50 more-specifics limit of the endpoint is reached;
- RIPEstat as-overview for every origin AS seen.

Each file is written as received, then its sha256 goes into raw/SHA256SUMS.
Python 3 standard library only.
"""
import hashlib
import ipaddress
import json
import os
import sys
import time
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ICI, "raw")
TIMESTAMP = "2026-10-14T16:00:00"  # RIS dump used by the article
LIMITE = 50  # routing-status returns at most 50 more-specifics
UA = {"User-Agent": "heurisme-lab/adressage-ip-radioamateur (https://github.com/feraudet/heurisme-lab)"}


def get(url):
    for essai in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # network hiccup: retry
            print(f"retry {essai + 1} {url}: {e}", file=sys.stderr)
            time.sleep(3 * (essai + 1))
    raise SystemExit(f"failed: {url}")


def ecrire(nom, contenu):
    chemin = os.path.join(RAW, nom)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "wb") as f:
        f.write(contenu)
    return contenu


def nom_prefixe(p):
    return str(p).replace("/", "_")


def routing_status(prefixe):
    url = ("https://stat.ripe.net/data/routing-status/data.json?resource=" + str(prefixe)
           + "&timestamp=" + TIMESTAMP + "&sourceapp=heurisme-lab")
    brut = ecrire(f"ripestat/routing-status_{nom_prefixe(prefixe)}.json", get(url))
    return json.loads(brut)["data"]


def parcourir(prefixe, vus):
    """Queries a prefix; if the more-specifics list is full, queries both halves."""
    data = routing_status(prefixe)
    vus.add(str(prefixe))
    if len(data["more_specifics"]) >= LIMITE and prefixe.prefixlen < 24:
        for moitie in prefixe.subnets(prefixlen_diff=1):
            parcourir(moitie, vus)


def main():
    os.makedirs(RAW, exist_ok=True)
    for p in ["44.0.0.0/8", "44.192.0.0/10", "44.0.0.0/9", "44.151.0.0/16"]:
        ecrire(f"rdap/arin_{nom_prefixe(p)}.json", get("https://rdap.arin.net/registry/ip/" + p))
    ecrire("rdap/arin_entity_ARDC.json", get("https://rdap.arin.net/registry/entity/ARDC"))
    ecrire("ripestat/ris-prefixes_AS56508.json",
           get("https://stat.ripe.net/data/ris-prefixes/data.json?resource=AS56508&list_prefixes=true"
               "&query_time=" + TIMESTAMP + "&sourceapp=heurisme-lab"))
    ecrire("ampr/geofeed.csv", get("https://portal.ampr.org/storage/geofeed.csv"))

    vus = set()
    parcourir(ipaddress.ip_network("44.0.0.0/8"), vus)
    # the French subnet, queried on its own: who covers it in BGP
    url = ("https://stat.ripe.net/data/routing-status/data.json?resource=44.151.0.0/16"
           "&timestamp=" + TIMESTAMP + "&sourceapp=heurisme-lab")
    ecrire("ripestat/france_routing-status_44.151.0.0_16.json", get(url))
    with open(os.path.join(RAW, "ripestat/queries.txt"), "w") as f:
        f.write("\n".join(sorted(vus, key=lambda s: ipaddress.ip_network(s))) + "\n")

    # origin AS of every prefix seen, for the holder names
    asns = set()
    for nom in os.listdir(os.path.join(RAW, "ripestat")):
        if nom.startswith("routing-status_"):
            d = json.load(open(os.path.join(RAW, "ripestat", nom)))["data"]
            asns.update(m["origin"] for m in d["more_specifics"])
            asns.update(o["origin"] for o in d["origins"])
    for asn in sorted(asns):
        ecrire(f"ripestat/as-overview_AS{asn}.json",
               get(f"https://stat.ripe.net/data/as-overview/data.json?resource=AS{asn}&sourceapp=heurisme-lab"))

    lignes = []
    for racine, _, fichiers in os.walk(RAW):
        for nom in fichiers:
            if nom == "SHA256SUMS":
                continue
            chemin = os.path.join(racine, nom)
            h = hashlib.sha256(open(chemin, "rb").read()).hexdigest()
            lignes.append(f"{h}  {os.path.relpath(chemin, RAW)}")
    with open(os.path.join(RAW, "SHA256SUMS"), "w") as f:
        f.write("\n".join(sorted(lignes, key=lambda l: l[66:])) + "\n")
    print(f"{len(vus)} routing-status queries, {len(asns)} origin AS, files in raw/")


if __name__ == "__main__":
    main()
