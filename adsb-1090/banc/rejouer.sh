#!/bin/sh
# Replays the whole bench. Run it from banc/: cd banc && sh rejouer.sh
# Requirements: Docker, curl, shasum (or sha256sum). No radio.
# The IQ file modes1.bin is downloaded into ../donnees/ then checked by sha256.
set -e
URL=https://github.com/antirez/dump1090/raw/master/testfiles/modes1.bin
SHA=3a33e16025da8669149c780075950b4e908ca036ea21f9583c113f60d5fb3094
mkdir -p ../donnees sorties
[ -f ../donnees/modes1.bin ] || curl -fsSL -o ../donnees/modes1.bin "$URL"
if command -v sha256sum >/dev/null; then H=$(sha256sum ../donnees/modes1.bin); else H=$(shasum -a 256 ../donnees/modes1.bin); fi
[ "${H%% *}" = "$SHA" ] || { echo "sha256 inattendu pour modes1.bin" >&2; exit 1; }
docker build -q -t adsb-banc .
R="docker run --rm -v $PWD:/banc -v $PWD/../donnees:/dl:ro -w /banc adsb-banc"
$R python3 adsb_main.py > sorties/01-main.txt
$R python3 demod_iq.py /dl/modes1.bin sorties/extrait.json > sorties/02-demod.txt
$R python3 demod_iq.py --court /dl/modes1.bin > sorties/02b-demod-court.txt
$R python3 adsb_pymodes.py > sorties/03-pymodes.txt
$R python3 paire_cpr.py > sorties/04-paire.txt
$R python3 -c "import numpy, sys; print('Python', sys.version.split()[0], ' numpy', numpy.__version__)" > sorties/00-versions.txt
# The sections shown slide by slide
$R python3 adsb_main.py 1 2 > sorties/05-champs-crc.txt
$R python3 adsb_main.py 3 4 > sorties/06-ident-alt.txt
$R python3 adsb_main.py 5 > sorties/07-cpr.txt
$R python3 adsb_main.py 6 > sorties/08-vitesse.txt
