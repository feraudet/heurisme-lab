#!/usr/bin/env python3
"""Runs the IAM policy simulator (aws iam simulate-custom-policy) on a deploy role that pushes
one object to S3, layer by layer, and prints a reduced, stable view of each answer.

usage: python3 simule.py default|boundary|deny|scp|commands

Each case calls the real IAM API (read only: nothing is created). The raw JSON answer goes to
brut/<case>.json (not kept in git); the output keeps EvalDecision, MatchedStatements and
MissingContextValues, plus the boundary and Organizations details when the API returns them.
The bucket ARN and the policies are examples: no bucket is read or written.
"""
import json
import os
import re
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
ACTION = "s3:PutObject"
RESOURCE = "arn:aws:s3:::amzn-s3-demo-bucket/releases/app-1.4.2.zip"
CALLER = "arn:aws:iam::111122223333:role/deploy"
OWNER = "arn:aws:iam::111122223333:root"

# case -> (group, label, identity policies, boundary, bucket policy, SCP levels, context)
# SCP levels: one list of SCP files per level, from the organization root down to the account.
CAS = [
    ("default", "A", "role allowed to read only", ["role-lecture.json"], None, None, None, []),
    ("default", "B", "role allowed to push", ["role-deploy.json"], None, None, None, []),
    ("boundary", "C", "push allowed, read-only boundary", ["role-deploy.json"], "boundary-lecture.json", None, None, []),
    ("boundary", "D", "push allowed, boundary that allows push", ["role-deploy.json"], "boundary-deploy.json", None, None, []),
    ("deny", "E", "bucket policy denies plain HTTP, request over HTTP", ["role-deploy.json"], "boundary-deploy.json",
     "bucket-https.json", None, [("aws:SecureTransport", "boolean", "false")]),
    ("deny", "F", "bucket policy denies plain HTTP, request over HTTPS", ["role-deploy.json"], "boundary-deploy.json",
     "bucket-https.json", None, [("aws:SecureTransport", "boolean", "true")]),
    ("deny", "G", "bucket policy denies plain HTTP, no context given", ["role-deploy.json"], "boundary-deploy.json",
     "bucket-https.json", None, []),
    ("scp", "H", "account SCP allows ec2:* only", ["role-deploy.json"], "boundary-deploy.json", None,
     [["scp-full-access.json"], ["scp-ec2-only.json"]], []),
    ("scp", "I", "SCP denies outside eu-west-3, request to us-east-1", ["role-deploy.json"], "boundary-deploy.json", None,
     [["scp-full-access.json"], ["scp-full-access.json", "scp-region.json"]], [("aws:RequestedRegion", "string", "us-east-1")]),
    ("scp", "J", "SCP denies outside eu-west-3, no context given", ["role-deploy.json"], "boundary-deploy.json", None,
     [["scp-full-access.json"], ["scp-full-access.json", "scp-region.json"]], []),
    ("scp", "K", "SCP denies outside eu-west-3, request to eu-west-3", ["role-deploy.json"], "boundary-deploy.json", None,
     [["scp-full-access.json"], ["scp-full-access.json", "scp-region.json"]], [("aws:RequestedRegion", "string", "eu-west-3")]),
]


def niveaux_scp(cas, niveaux):
    """Writes policies/org-<case>.json: the SCP levels as the API expects them (each SCP as a JSON string)."""
    nom = f"org-{cas}.json"
    liste = []
    for niveau in niveaux:
        docs = []
        for f in niveau:
            with open(os.path.join(ICI, "policies", f), encoding="utf-8") as h:
                docs.append(json.dumps(json.load(h), separators=(",", ":")))
        liste.append({"ServiceControlPolicyInputList": docs})
    with open(os.path.join(ICI, "policies", nom), "w", encoding="utf-8") as h:
        json.dump(liste, h, indent=2)
        h.write("\n")
    return nom


class Contenu(str):
    """A policy file passed as its content: the list parameters of the AWS CLI read a file:// as a
    JSON list, not as one policy, so the text goes on the command line (shown as "$(cat file)")."""

    def __new__(cls, f):
        with open(os.path.join(ICI, "policies", f), encoding="utf-8") as h:
            obj = super().__new__(cls, h.read())
        obj.affiche = f'"$(cat policies/{f})"'
        return obj


def commande(c):
    _, lettre, _, ident, boundary, bucket, scp, ctx = c
    args = ["aws", "iam", "simulate-custom-policy", "--action-names", ACTION, "--resource-arns", RESOURCE,
            "--policy-input-list"] + [Contenu(f) for f in ident]
    if boundary:
        args += ["--permissions-boundary-policy-input-list", Contenu(boundary)]
    if bucket:
        args += ["--resource-policy", f"file://policies/{bucket}", "--caller-arn", CALLER, "--resource-owner", OWNER]
    if scp:
        args += ["--ordered-organization-policy-input-list", f"file://policies/{niveaux_scp(lettre, scp)}"]
    for cle, typ, val in ctx:
        args += ["--context-entries", f"ContextKeyName={cle},ContextKeyType={typ},ContextKeyValues={val}"]
    return args + ["--output", "json"]


def couches(c):
    """The policy files of a case, without .json, SCPs as root > account ("scp-" dropped)."""
    _, _, _, ident, boundary, bucket, scp, _ = c
    nom = lambda f: f[:-5]
    out = [nom(f) for f in ident]
    if boundary:
        out.append(nom(boundary))
    if bucket:
        out.append(nom(bucket))
    if scp:
        out.append("SCP " + " > ".join("+".join(nom(f)[4:] for f in n) for n in scp))
    return out


def lignes(st):
    deb, fin = st.get("StartPosition", {}), st.get("EndPosition", {})
    return f"lines {deb.get('Line', '?')}-{fin.get('Line', '?')}"


def reduire(rep):
    """Keeps the fields that explain the decision, in a fixed order."""
    out = []
    for r in sorted(rep.get("EvaluationResults", []), key=lambda r: (r.get("EvalActionName", ""), r.get("EvalResourceName", ""))):
        out.append(f"  EvalDecision          {r['EvalDecision']}")
        ms = sorted(r.get("MatchedStatements", []), key=lambda s: (s.get("SourcePolicyId", ""), lignes(s)))
        if ms:
            for n, s in enumerate(ms):
                tete = "  MatchedStatements     " if n == 0 else "                        "
                out.append(f"{tete}{s.get('SourcePolicyId', '?')} ({s.get('SourcePolicyType', '?')}) {lignes(s)}")
        else:
            out.append("  MatchedStatements     (none)")
        mc = sorted(r.get("MissingContextValues", []))
        out.append("  MissingContextValues  " + (", ".join(mc) if mc else "(none)"))
        pb = r.get("PermissionsBoundaryDecisionDetail")
        if pb is not None:
            out.append(f"  AllowedByPermissionsBoundary  {str(pb.get('AllowedByPermissionsBoundary')).lower()}")
        org = r.get("OrganizationsDecisionDetail")
        if org is not None:
            out.append(f"  AllowedByOrganizations        {str(org.get('AllowedByOrganizations')).lower()}")
    return out


def main():
    groupe = sys.argv[1] if len(sys.argv) > 1 else ""
    if groupe not in ("default", "boundary", "deny", "scp", "commands"):
        sys.exit(__doc__)
    os.chdir(ICI)
    if groupe == "commands":
        for c in CAS:
            print(f"# {c[1]}. {c[2]}")
            print(" ".join(getattr(x, "affiche", x) for x in commande(c)))
        return
    print(f"$ python3 simule.py {groupe}")
    print(f"action    {ACTION}")
    print(f"resource  {RESOURCE}")
    groupe_cas = [c for c in CAS if c[0] == groupe]
    communes = [x for x in couches(groupe_cas[0]) if all(x in couches(c) for c in groupe_cas)]
    if communes:
        print(f"policies  {', '.join(communes)} (every case below)")
    os.makedirs("brut", exist_ok=True)
    for c in CAS:
        if c[0] != groupe:
            continue
        _, lettre, titre, ident, boundary, bucket, scp, ctx = c
        print()
        print(f"[{lettre}] {titre}")
        # one line: the policy files that differ from the common ones, then the context
        propres = [x for x in couches(c) if x not in communes]
        contexte = ", ".join(f"{k}={v}" for k, _, v in ctx) if ctx else "(none)"
        print("    " + (", ".join(propres) + "   " if propres else "") + "context: " + contexte)
        r = subprocess.run(commande(c), capture_output=True, text=True)
        if r.returncode != 0:
            # never print the caller's account number
            print("  error: " + re.sub(r"\b(?!111122223333)\d{12}\b", "<account>", r.stderr.strip().splitlines()[-1]))
            continue
        with open(os.path.join("brut", f"{lettre}.json"), "w", encoding="utf-8") as h:
            h.write(r.stdout)
        for ligne in reduire(json.loads(r.stdout)):
            print(ligne)


if __name__ == "__main__":
    main()
