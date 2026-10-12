#!/bin/sh
# Step 2, in the fx-mustang image: offline validation of a Factur-X PDF.
# Run from banc/: docker run --rm -v "$PWD":/banc fx-mustang sh 2-valider.sh sortie/facture.pdf
# The XML report (stdout) and the log (stderr) are kept separate.
cd "$(dirname "$1")"
echo "\$ java -jar /opt/mustang.jar --action validate --source $(basename "$1") --disable-file-logging 2>$(basename "$1" .pdf).journal.txt"
java -jar /opt/mustang.jar --action validate --source "$(basename "$1")" --disable-file-logging 2>"$(basename "$1" .pdf).journal.txt"
echo "[exit $?]"
