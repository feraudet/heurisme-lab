#!/usr/bin/env python3
"""The script that calls the internal API: trusts the root of the local PKI, and nothing else."""
import ssl
import urllib.request

contexte = ssl.create_default_context(cafile="pki/racine.crt")
with urllib.request.urlopen("https://www.exemple.test/api/sante", context=contexte) as reponse:
    print(reponse.status, reponse.read().decode().strip())
