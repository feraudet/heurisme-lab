#!/bin/bash
# Run inside the deck-ax25-dw container (debian:trixie-20251117 + snapshot 2025-12-09, linux/arm64), user ham, cwd /w/work.
# Each raw output goes to /w/raw/<n>-<name>.ansi (direwolf colour codes included),
# then a copy without the ANSI sequences goes to /w/raw/<n>-<name>.txt.
set -u
cd /w/work
R=/w/raw
clean() { sed -e 's/\x1b\[[0-9;]*[A-Za-z]//g' "$R/$1.ansi" > "$R/$1.txt"; }
run() { # run <name> <command...>: writes "$ command" then its output
  local nom=$1; shift
  { echo "\$ $*"; bash -c "$*" 2>&1; echo "(exit $?)"; } >> "$R/$nom.ansi"
}

printf 'F1TMV-7>APRS,WIDE1-1,WIDE2-1:!4903.50N/07201.75W-Test' > p1.txt
printf 'F1TMV-7>APRS,N0CALL-1*,WIDE2-1:!4903.50N/07201.75W-Test' > p2.txt
printf 'F1TMV-7>APRS,N0CALL-2*,WIDE2-1:!4903.50N/07201.75W-Test' > p3.txt

rm -f $R/0[0-5]-*.ansi $R/0[0-5]-*.txt

run 00-versions 'cat /etc/debian_version; uname -m; dpkg-query -W direwolf; direwolf -h 2>&1 | head -1'
clean 00-versions

run 01-aller-retour 'cat p1.txt; echo'
run 01-aller-retour 'gen_packets -o p1.wav p1.txt'
run 01-aller-retour 'atest -h p1.wav'
clean 01-aller-retour

run 02-digi 'cat digi.conf'
run 02-digi 'cat p1.txt; echo; cat p3.txt; echo'
run 02-digi 'gen_packets -o p1.wav p1.txt; gen_packets -o p3.wav p3.txt'
# stdin, at real-time rate (pv -L 88200 bytes/s = 44100 16-bit samples): 2 s of silence, p1, 4 s of silence, p3 (same frame heard through another digi), 4 s of silence
run 02-digi '(head -c 176400 /dev/zero; tail -c +45 p1.wav; head -c 352800 /dev/zero; tail -c +45 p3.wav; head -c 352800 /dev/zero) | pv -q -L 88200 | direwolf -c digi.conf -t 0 -r 44100 -'
clean 02-digi

run 03-trame-digi 'cat p2.txt; echo'
run 03-trame-digi 'gen_packets -o p2.wav p2.txt'
run 03-trame-digi 'atest -h p2.wav'
clean 03-trame-digi

run 04-9600 'gen_packets -B 9600 -r 48000 -o p9600.wav p1.txt'
run 04-9600 'atest -B 9600 p9600.wav'
run 04-9600 'atest -B 1200 p9600.wav'
clean 04-9600

# KISS: direwolf decodes p1.wav (stdin, real-time rate) and hands it to the TCP client on port 8001
run 05-kiss 'cat kiss.conf'
run 05-kiss '((head -c 176400 /dev/zero; tail -c +45 p1.wav; head -c 176400 /dev/zero) | pv -q -L 88200 | direwolf -c kiss.conf -t 0 -r 44100 - > /dev/null 2>&1 &) ; python3 kiss_client.py 4'
clean 05-kiss
