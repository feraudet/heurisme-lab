#!/bin/sh
# Step 7, in the fx-py image: the same invoice without electronic address (BT-34 and BT-49).
# Then: docker run --rm -v "$PWD":/banc fx-mustang sh 2-valider.sh sortie/sans-adresse.pdf
# Run from banc/: docker run --rm -v "$PWD":/banc fx-py sh 7-sans-adresse.sh
python3 - <<'PY'
import re
s = open("factur-x.xml", encoding="utf-8").read()
s = re.sub(r"\s*<ram:URIUniversalCommunication>.*?</ram:URIUniversalCommunication>", "", s, flags=re.S)
open("sortie/sans-adresse.xml", "w", encoding="utf-8").write(s)
PY
cd sortie
facturx-pdfgen -w visuel-pdfa.pdf sans-adresse.xml sans-adresse.pdf > sans-adresse.pdfgen.txt 2>&1
echo "facturx-pdfgen : exit $?"
