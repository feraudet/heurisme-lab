#!/bin/sh
# Step 8, in the fx-py image: same page converted by Ghostscript WITHOUT the pdfa-def.ps file (hence without OutputIntent).
# Then: docker run --rm -v "$PWD":/banc fx-mustang sh 2-valider.sh sortie/sans-profil.pdf
gs -q -dPDFA=3 -dBATCH -dNOPAUSE -sColorConversionStrategy=RGB -dPDFACompatibilityPolicy=1 \
   -sDEVICE=pdfwrite -o sortie/sans-profil-pdfa.pdf sortie/visuel.pdf
facturx-pdfgen -w sortie/sans-profil-pdfa.pdf factur-x.xml sortie/sans-profil.pdf > sortie/sans-profil.pdfgen.txt 2>&1
echo "facturx-pdfgen : exit $?"
