#!/bin/bash
# Replays the Scion bench of the article https://heurisme.fr/en/blog/scion-git-agents/
# Needs git and python3 (no package). Measured with git 2.55.0 and Python 3.14.7 on macOS arm64, 16 CPU.
# Takes about 7 minutes: 200 agents pushing to one bare repo is the slow part.
set -eu
cd "$(dirname "$0")"
mkdir -p raw
python3 course_push.py > raw/course_push.txt 2>&1
echo "Sortie dans raw/course_push.txt. Durées et compteurs changent d'un run à l'autre (vraie course entre processus)."
