#!/bin/bash
# Creates the local PKI in pki/: a root, an intermediate, a leaf for www.exemple.test.
# Keys are generated at each replay (EC P-256), so signatures, key identifiers and
# fingerprints change from one replay to the next. Subjects, issuers, serial numbers and
# validity dates do not: the dates are fixed by -startdate / -enddate, the serial numbers
# by the pki/serial file.
set -eu
cd "$(dirname "$0")"
rm -rf pki && mkdir -p pki/emis
touch pki/index.txt
DEBUT=20261001000000Z
FIN=20361001000000Z

cle() { openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "pki/$1.key" 2>/dev/null; }
signe() { # name, CN, extensions, signing key, issuer certificate (empty: self-signed)
  openssl req -new -config ca.cnf -key "pki/$1.key" -subj "/CN=$2" -out "pki/$1.csr"
  if [ -z "$5" ]; then
    openssl ca -batch -config ca.cnf -selfsign -keyfile "pki/$4.key" -startdate $DEBUT -enddate $FIN \
      -extensions "$3" -notext -in "pki/$1.csr" -out "pki/$1.crt" 2>/dev/null
  else
    openssl ca -batch -config ca.cnf -keyfile "pki/$4.key" -cert "pki/$5.crt" -startdate $DEBUT -enddate $FIN \
      -extensions "$3" -notext -in "pki/$1.csr" -out "pki/$1.crt" 2>/dev/null
  fi
}

echo 1001 > pki/serial; cle racine;        signe racine        "Exemple Racine"        ext_racine        racine        ""
echo 2001 > pki/serial; cle intermediaire; signe intermediaire "Exemple Intermediaire" ext_intermediaire racine        racine
echo 3001 > pki/serial; cle feuille;       signe feuille       "www.exemple.test"      ext_feuille       intermediaire intermediaire

# what nginx serves: the leaf alone, or the leaf followed by the intermediate (fullchain)
cp pki/feuille.crt pki/feuille-seule.pem
cat pki/feuille.crt pki/intermediaire.crt > pki/fullchain.pem
# the wrong order, to see what nginx says
cat pki/intermediaire.crt pki/feuille.crt > pki/fullchain-a-l-envers.pem
# the intermediate published at the caIssuers address of the leaf (DER, as RFC 5280 asks)
mkdir -p pki/www-pki
openssl x509 -in pki/intermediaire.crt -outform DER -out pki/www-pki/intermediaire.crt
