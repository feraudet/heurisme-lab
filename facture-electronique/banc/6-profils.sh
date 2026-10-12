#!/bin/sh
# Step 6, in the fx-py image: the same XML checked against the XSD and the Schematron of each Factur-X profile.
# Run from banc/: docker run --rm -v "$PWD":/banc fx-py sh 6-profils.sh [--en]
O="${1:+$1 }"
echo "\$ python profils.py ${O}factur-x.xml"
python profils.py $1 factur-x.xml
echo "[exit $?]"
