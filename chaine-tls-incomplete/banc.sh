#!/bin/bash
# Runs inside the container: creates the PKI, then plays the four cases and writes sorties/01 to 07.
# Each output file starts with the command, prefixed by "$ ".
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"
bash pki.sh

lance() { echo "\$ $1"; bash -o pipefail -c "$1" 2>&1; echo "(exit $?)"; }
# s_client prints the certificates in PEM and the TLS session: the PEM body, the session
# identifiers, the byte counts and the start time change at each replay, masque.py hides them.
s_client() { echo "\$ openssl s_client -connect www.exemple.test:443 -servername www.exemple.test -CAfile pki/racine.crt -showcerts </dev/null"
  openssl s_client -connect www.exemple.test:443 -servername www.exemple.test -CAfile pki/racine.crt -showcerts </dev/null 2>&1 | python3 masque.py
  echo "(exit ${PIPESTATUS[0]})"; }

{ lance 'openssl x509 -in pki/racine.crt -noout -subject -issuer -serial -dates'
  lance 'openssl x509 -in pki/intermediaire.crt -noout -subject -issuer -serial -ext basicConstraints'
  lance 'openssl x509 -in pki/feuille.crt -noout -subject -issuer -serial -ext subjectAltName,authorityInfoAccess'
} > sorties/01-pki.txt

# Case 1: nginx serves the leaf alone
nginx -c /w/nginx-feuille-seule.conf
{ lance 'grep ssl_certificate nginx-feuille-seule.conf'
  s_client
} > sorties/02-feuille-seule-s_client.txt
{ lance 'curl -sS https://www.exemple.test/api/sante --cacert pki/racine.crt'
  lance 'python3 client.py 2>&1 | tail -n 1'
  lance 'openssl verify -CAfile pki/racine.crt pki/feuille.crt'
} > sorties/03-feuille-seule-clients.txt

# What a browser does on its own: follow the caIssuers address of the leaf, then verify again
{ lance 'openssl x509 -in pki/feuille.crt -noout -ext authorityInfoAccess'
  lance 'curl -s http://pki.exemple.test/intermediaire.crt -o /tmp/intermediaire.der -w "%{http_code} %{content_type}\n"'
  lance 'openssl x509 -inform DER -in /tmp/intermediaire.der -out /tmp/intermediaire.pem && openssl x509 -in /tmp/intermediaire.pem -noout -subject -issuer'
  lance 'openssl verify -CAfile pki/racine.crt -untrusted /tmp/intermediaire.pem pki/feuille.crt'
} > sorties/04-aia-a-la-main.txt

# Case 2: nginx serves the full chain (leaf, then intermediate)
nginx -s stop -c /w/nginx-feuille-seule.conf; sleep 1
nginx -c /w/nginx-fullchain.conf
{ lance 'grep ssl_certificate nginx-fullchain.conf'
  lance 'grep -c "BEGIN CERTIFICATE" pki/fullchain.pem'
  s_client
} > sorties/05-fullchain-s_client.txt
{ lance 'curl -sS https://www.exemple.test/api/sante --cacert pki/racine.crt'
  lance 'python3 client.py 2>&1 | tail -n 1'
} > sorties/06-fullchain-clients.txt
nginx -s stop -c /w/nginx-fullchain.conf; sleep 1

# Case 3: the same two certificates in the wrong order
# nginx starts its error line with the date and its process id: both masked.
{ echo '$ nginx -t -c /w/nginx-fullchain-a-l-envers.conf'
  nginx -t -c /w/nginx-fullchain-a-l-envers.conf 2>&1 | sed -E 's|^[0-9]{4}/[0-9]{2}/[0-9]{2} [0-9:]{8} \[emerg\] [0-9]+#[0-9]+:|(date masked) [emerg] (pid masked):|'
  echo "(exit ${PIPESTATUS[0]})"
} > sorties/07-ordre-inverse.txt
