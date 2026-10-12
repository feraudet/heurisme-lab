#!/bin/sh
# Step 5, in the fx-py image: open the PDF layer by layer and read the fields of the attached XML.
# Run from banc/: docker run --rm -v "$PWD":/banc fx-py sh 5-inspecter.sh [--en]
O="${1:+$1 }"
cd sortie
echo "\$ python couches.py ${O}facture.pdf"
python ../couches.py $1 facture.pdf
echo "[exit $?]"
echo "\$ python champs.py ${O}facture.pdf"
python ../champs.py $1 facture.pdf
echo "[exit $?]"
