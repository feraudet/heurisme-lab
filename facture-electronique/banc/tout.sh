#!/bin/sh
# Replay the whole bench from scratch, on a machine with Docker. Run from banc/: sh tout.sh
# Downloads Mustang CLI 2.24.0 (third-party data, not copied into the repo) and checks its sha256.
set -e
cd "$(dirname "$0")"
curl -fsSL https://repo1.maven.org/maven2/org/mustangproject/Mustang-CLI/2.24.0/Mustang-CLI-2.24.0.jar -o Mustang-CLI-2.24.0.jar
echo "e4904ffa0afdce3f5836dceb927c440a05ed5d60386fdd37e17a4b2f7652edbf  Mustang-CLI-2.24.0.jar" | shasum -a 256 -c -
docker build -q -t fx-py -f Dockerfile.py .
docker build -q -t fx-mustang -f Dockerfile.mustang .
rm -f Mustang-CLI-2.24.0.jar
rm -rf sortie && mkdir sortie
docker run --rm -v "$PWD":/banc fx-py sh 1-generer.sh > sortie/1-generer.txt 2>&1
docker run --rm -v "$PWD":/banc fx-mustang sh 2-valider.sh sortie/facture.pdf > sortie/2-valider.txt
docker run --rm -v "$PWD":/banc fx-py sh 3-fausser.sh > sortie/3-fausser.txt 2>&1
for v in faux-total faux-tva faux-centimes; do
  docker run --rm -v "$PWD":/banc fx-mustang sh 2-valider.sh sortie/$v.pdf > sortie/4-valider-$v.txt || true
done
docker run --rm -v "$PWD":/banc fx-py sh 5-inspecter.sh > sortie/5-inspecter.txt 2>&1
docker run --rm -v "$PWD":/banc fx-py sh 6-profils.sh > sortie/6-profils.txt 2>&1
docker run --rm -v "$PWD":/banc fx-py sh 5-inspecter.sh --en > sortie/5-inspecter-en.txt 2>&1
docker run --rm -v "$PWD":/banc fx-py sh 6-profils.sh --en > sortie/6-profils-en.txt 2>&1
docker run --rm -v "$PWD":/banc fx-py sh 7-sans-adresse.sh > sortie/7-sans-adresse.txt 2>&1
docker run --rm -v "$PWD":/banc fx-mustang sh 2-valider.sh sortie/sans-adresse.pdf > sortie/7-valider-sans-adresse.txt || true
docker run --rm -v "$PWD":/banc fx-py sh 8-sans-profil.sh > sortie/8-sans-profil.txt 2>&1
docker run --rm -v "$PWD":/banc fx-mustang sh 2-valider.sh sortie/sans-profil.pdf > sortie/8-valider-sans-profil.txt || true
echo fini
