#!/usr/bin/env python3
"""Reads raw/ (written by collecte.py) and prints the figures of the deck. No network.

  python3 analyse.py rdap     who holds 44.0.0.0/8 according to ARIN
  python3 analyse.py bgp      what is announced in BGP inside 44.0.0.0/8
  python3 analyse.py france   the French subnet 44.151.0.0/16: geofeed and BGP

Output is plain text, sorted, with no clock time: two runs on the same raw/ give the same bytes.
Python 3 standard library only.
"""
import collections
import csv
import glob
import ipaddress
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ICI, "raw")
BLOCS = ["44.0.0.0/9", "44.128.0.0/10", "44.192.0.0/10"]
FRANCE = ipaddress.ip_network("44.151.0.0/16")


def lire(chemin):
    with open(os.path.join(RAW, chemin)) as f:
        return json.load(f)


def nom_fn(entite):
    for v in entite.get("vcardArray", [None, []])[1]:
        if v[0] == "fn":
            return v[3]
    return ""


def rdap():
    for p in ["44.0.0.0/8", "44.0.0.0/9", "44.151.0.0/16", "44.192.0.0/10"]:
        d = lire(f"rdap/arin_{p.replace('/', '_')}.json")
        ev = {e["eventAction"]: e["eventDate"][:10] for e in d.get("events", [])}
        cidrs = ", ".join(f"{c['v4prefix']}/{c['length']}" for c in d.get("cidr0_cidrs", []))
        qui = ", ".join(f"{e['handle']} ({nom_fn(e)})" for e in d.get("entities", []))
        print(f"query {p} -> {d['handle']} ({d.get('name')})")
        print(f"  {d['startAddress']} - {d['endAddress']} = {cidrs}")
        print(f"  registrant {qui}")
        print(f"  registered {ev.get('registration')}, last changed {ev.get('last changed')}")
    d = lire("rdap/arin_entity_ARDC.json")
    print(f"ARIN entity ARDC ({nom_fn(d)}): {len(d.get('networks', []))} network(s)")
    for n in d.get("networks", []):
        print(f"  {n['handle']}  {n['startAddress']} - {n['endAddress']}  ipVersion {n.get('ipVersion')}")
    d = lire("ripestat/ris-prefixes_AS56508.json")["data"]
    c = d["counts"]
    print(f"AS56508 ({nom_as(56508)}) originates: {c['v4']['originating']} IPv4 prefix(es), {c['v6']['originating']} IPv6 prefix(es)")


def annonces():
    """Union of all (prefix, origin AS) seen in the routing-status answers."""
    vus = set()
    for f in glob.glob(os.path.join(RAW, "ripestat", "routing-status_*.json")):
        d = json.load(open(f))["data"]
        for m in d["more_specifics"]:
            vus.add((m["prefix"], m["origin"]))
        for o in d["origins"]:
            vus.add((d["resource"], o["origin"]))
    return sorted(((ipaddress.ip_network(p), a) for p, a in vus), key=lambda x: (x[0], x[1]))


def nom_as(asn):
    f = os.path.join(RAW, "ripestat", f"as-overview_AS{asn}.json")
    if not os.path.exists(f):
        return "?"
    return json.load(open(f))["data"].get("holder") or "?"


def adresses(prefixes):
    """Number of distinct addresses covered (overlaps counted once)."""
    return sum(n.num_addresses for n in ipaddress.collapse_addresses(prefixes))


def bgp():
    rs = lire("ripestat/routing-status_44.0.0.0_8.json")["data"]
    lignes = annonces()
    prefixes = sorted({p for p, _ in lignes})
    print(f"RIS dump {rs['query_time']} UTC, routes seen by at least 10 RIS peers (RIPEstat routing-status default)")
    print(f"44.0.0.0/8 itself announced: {'yes' if rs['origins'] else 'no'}")
    print(f"distinct prefixes announced inside 44.0.0.0/8: {len(prefixes)}")
    print(f"distinct (prefix, origin AS) pairs: {len(lignes)}")
    print(f"distinct origin AS: {len({a for _, a in lignes})}")
    print()
    longueurs = collections.Counter(p.prefixlen for p in prefixes)
    print("prefixes by length: " + ", ".join(f"/{l} x{longueurs[l]}" for l in sorted(longueurs)))
    print(f"longest prefix announced: /{max(longueurs)}")
    print()
    print("by block               prefixes   more specifics   addresses in more specifics")
    for b in BLOCS:
        bloc = ipaddress.ip_network(b)
        dedans = [p for p in prefixes if p.subnet_of(bloc)]
        fins = [p for p in dedans if p.prefixlen > bloc.prefixlen]
        n = adresses(fins)
        print(f"  {b:<19} {len(dedans):>8}   {len(fins):>14}   {n:>11,} ({100 * n / bloc.num_addresses:.2f} % of the block)")
    print()
    tous = adresses(prefixes)
    amazon = adresses([p for p, a in lignes if a in (16509, 14618)])
    print(f"addresses covered by an announcement inside 44.0.0.0/8: {tous:,}")
    print(f"  of which originated by Amazon (AS16509, AS14618): {amazon:,} ({100 * amazon / tous:.2f} %)")
    print()
    print("covering routes of the three blocks")
    for p, a in lignes:
        if str(p) in ("44.0.0.0/9", "44.128.0.0/10", "44.192.0.0/10", "44.192.0.0/11", "44.224.0.0/11"):
            print(f"  {str(p):<16} AS{a:<7} {nom_as(a)}")
    print()
    hors_amazon = [(p, a) for p, a in lignes if not p.subnet_of(ipaddress.ip_network("44.192.0.0/10"))]
    print("top 10 origin AS inside 44.0.0.0/9 and 44.128.0.0/10, by number of prefixes")
    par_as = collections.Counter(a for p, a in hors_amazon)
    for a, n in sorted(par_as.items(), key=lambda x: (-x[1], x[0]))[:10]:
        print(f"  AS{a:<7} {n:>4}  {nom_as(a)}")


def geofeed():
    with open(os.path.join(RAW, "ampr", "geofeed.csv"), newline="") as f:
        return [r for r in csv.reader(f) if r and not r[0].startswith("#")]


def france():
    lignes = geofeed()
    pays = collections.Counter(r[1] for r in lignes)
    print(f"AMPRNet geofeed (portal.ampr.org): {len(lignes)} entries, {len(pays)} country codes")
    print("top 5 countries by number of entries")
    for c, n in sorted(pays.items(), key=lambda x: (-x[1], x[0]))[:5]:
        print(f"  {c}  {n:>5}")
    fr = [r for r in lignes if r[1] == "FR"]
    print(f"FR entries: {len(fr)}")
    print()
    dans = [r for r in fr if ipaddress.ip_network(r[0]).subnet_of(FRANCE)]
    hors = [r for r in fr if not ipaddress.ip_network(r[0]).subnet_of(FRANCE)]
    print(f"FR entries inside 44.151.0.0/16: {len(dans)}")
    longueurs = collections.Counter(ipaddress.ip_network(r[0]).prefixlen for r in dans)
    print("  by length: " + ", ".join(f"/{l} x{longueurs[l]}" for l in sorted(longueurs)))
    print(f"  first line: {','.join(next(r for r in dans if r[0] == '44.151.0.0/16'))}")
    print(f"FR entries outside 44.151.0.0/16: {len(hors)}")
    print()
    rs = lire("ripestat/france_routing-status_44.151.0.0_16.json")["data"]
    print(f"BGP for 44.151.0.0/16 (RIS dump {rs['query_time']} UTC)")
    print(f"  announced itself: {'yes' if rs['origins'] else 'no'}")
    print(f"  more specifics announced: {len(rs['more_specifics'])}")
    for m in rs["less_specifics"]:
        print(f"  covered by: {m['prefix']} AS{m['origin']} {nom_as(m['origin'])}")
    print()
    # AS numbers only: several of these AS are held by private persons
    print("FR geofeed entries that match a BGP announcement exactly (all outside 44.151.0.0/16)")
    annonce = {}
    for p, a in annonces():
        annonce.setdefault(p, []).append(a)
    n = 0
    for r in sorted(fr, key=lambda r: ipaddress.ip_network(r[0])):
        p = ipaddress.ip_network(r[0])
        if p in annonce:
            n += 1
            assert not p.subnet_of(FRANCE)
            print(f"  {r[0]:<18} " + " ".join(f"AS{a}" for a in annonce[p]))
    print(f"  total: {n} of {len(fr)} FR entries")


if __name__ == "__main__":
    {"rdap": rdap, "bgp": bgp, "france": france}[sys.argv[1]]()
