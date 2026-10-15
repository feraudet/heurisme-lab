#!/bin/bash
# Runs inside the container: writes the NEC2 decks, runs nec2c on each, then writes sorties/.
set -eu
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"
rm -f nec/*.nec nec/*.out
python3 antenne.py > /dev/null
for d in nec/*.nec; do
  nec2c -i "$d" -o "${d%.nec}.out"
done
mkdir -p sorties
{ echo '$ python3 ros.py ros'; python3 ros.py ros; echo "(exit $?)"; } > sorties/01-ros.txt
{ echo '$ python3 lit_nec.py'; python3 lit_nec.py; echo "(exit $?)"; } > sorties/02-nec.txt
{ echo '$ python3 ros.py cable'; python3 ros.py cable; echo "(exit $?)"; } > sorties/03-cable.txt
