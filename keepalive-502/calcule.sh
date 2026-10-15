#!/bin/bash
# Runs inside the container: the four scenarios of the deck, written to sorties/.
# About 30 minutes: each run lasts about two minutes (23 pauses of 3 to 7 s, 20 lanes side by side).
set -eu
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"
mkdir -p sorties run
# 1. the bug: Node.js closes after 5 s (its default), nginx keeps idle connections 60 s
python3 scenario.py default 60s POST 5 > sorties/01-post-5s-60s.txt 2>/dev/null
# 2. same bug, GET requests: nginx retries them on a new connection
python3 scenario.py default 60s GET 3 > sorties/02-get-5s-60s.txt 2>/dev/null
# 3. fix on the backend: Node.js keeps idle connections 65 s, longer than nginx
python3 scenario.py 65000 60s POST 3 > sorties/03-post-65s-60s.txt 2>/dev/null
# 4. fix on the proxy: nginx forgets idle connections after 4 s, before Node.js closes them
python3 scenario.py default 4s POST 3 > sorties/04-post-5s-4s.txt 2>/dev/null
