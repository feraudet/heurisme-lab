#!/bin/sh
# Step 1, in the fx-py image: readable PDF, PDF/A-3b conversion, then Factur-X.
# Run from banc/: docker run --rm -v "$PWD":/banc fx-py sh 1-generer.sh
set -e
mkdir -p sortie
python visuel.py sortie/visuel.pdf
gs -q -dPDFA=3 -dBATCH -dNOPAUSE -sColorConversionStrategy=RGB -sProcessColorModel=DeviceRGB \
   --permit-file-read=/usr/share/color/icc/ghostscript/srgb.icc -dPDFACompatibilityPolicy=1 \
   -sDEVICE=pdfwrite -o sortie/visuel-pdfa.pdf ./pdfa-def.ps sortie/visuel.pdf
echo '$ facturx-pdfgen -w sortie/visuel-pdfa.pdf factur-x.xml sortie/facture.pdf'
facturx-pdfgen -w sortie/visuel-pdfa.pdf factur-x.xml sortie/facture.pdf 2>&1
echo "[exit $?]"
