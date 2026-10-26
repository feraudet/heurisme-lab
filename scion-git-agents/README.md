# Scion bench: N agents push to one repo

This bench goes with the article https://heurisme.fr/en/blog/scion-git-agents/ on Scion, the source control system Anthropic built to replace git in their monorepo (source: https://www.anthropic.com/engineering/redesigning-source-control, 13 October 2026). Scion is not public. The bench does not run Scion: it replays with real git the problem Scion solves (N agents pushing to the same repo) and compares it with the Scion model, where the server builds the commits and advances main by compare-and-swap.

File names and outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `raw/` = raw outputs, `course_push.py` = push race, `agent` = agent, `refus` = rejection, `verrou` = lock, `durée` = duration, `fichiers` = files, `CAS ratés` = failed CAS, `modèle` = model.

## How to replay

- git and python3, no package.
- Measured with git 2.55.0 and Python 3.14.7 on macOS arm64, 16 CPU.

Single command:

```bash
bash rejouer.sh
```

It runs `course_push.py` and rewrites `raw/course_push.txt`. Takes about 7 minutes: 200 agents pushing to one bare repo is the slow part. Durations and counters change from one run to the next (real race between processes). The orders of magnitude stay.

## Section 1: Anthropic's numbers, recomputed

25 M CI checkouts per day x 25 GB = 625 PB per day (the article says "over 600 PB"). 2,500 merges per day in May 2026, over 30,000 in September: x12. 30,000 per day = one merge every 2.9 s.

## Section 2: model A, classic git

Each agent has its own clone (prepared before the clock starts), one commit on its own file (no possible conflict), then `git push`. Rejected, it runs `git fetch` then `git rebase origin/main` and pushes again. All agents start at the same time (thread barrier). N = 1, 10, 50, 200.

| N agents | pushes | non-fast-forward rejections | lock rejections | rebases | worst agent | duration |
|---|---|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 0 | 1 | 0.1 s |
| 10 | 55 | 0 | 45 | 45 | 10 | 1.3 s |
| 50 | 1,240 | 676 | 514 | 1,190 | 49 | 21.2 s |
| 200 | 17,031 | 13,657 | 3,174 | 16,831 | 180 | 367.5 s |

At 10 agents: 55 pushes = 10 + 9 + ... + 1.

## Section 3: model B, server-side merge

The same workload arrives as changesets. The server builds each commit in the bare repo with git plumbing (`read-tree` of the tip into a temporary index, `update-index --add --cacheinfo`, `write-tree`, `commit-tree -p <tip>`), then `git update-ref refs/heads/main <new> <old>`, which fails if main has moved: that is the compare-and-swap. A failed CAS retries on the new tip.

| threads | changesets | CAS succeeded | CAS failed | duration |
|---|---|---|---|---|
| 1 | 200 | 200 | 0 | 10.3 s |
| 8 | 200 | 200 | 1,351 | 14.2 s |

With 1 thread: 200 commits in 10.3 s, zero failed CAS. With 8 threads: 14.2 s and 1,351 failed CAS, because each attempt runs five git commands.

## Section to slide

| Section of `raw/course_push.txt` | Slide |
|---|---|
| 1 (Anthropic's numbers) | 2 |
| 2 (model A, classic git) | 6 |
| 3 (model B, server-side merge) | 7 |

## What is simulated

The bench runs on a single machine, not over a network. The CAS operates on a git ref file, not a Spanner row. Agents touch different files, so there is no real conflict. Git automatic gc and maintenance are disabled (`gc.auto=0`, `maintenance.auto=false`) because they clean up `objects/` while a rebase writes to it ("unable to create temporary file", found during development). An error from any agent stops the bench instead of producing a wrong number.

## Third-party data

None. Anthropic's numbers come from the article cited above.
