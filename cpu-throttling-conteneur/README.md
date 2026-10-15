# cpu-throttling-conteneur

This bench goes with the deck https://heurisme.fr/en/blog/cpu-throttling-conteneur/ : why a CPU limit on a container slows down a multi-threaded service even when the machine is idle. The same small API runs four times: with no limit, with `--cpus=1` (CFS quota of 100 ms every 100 ms), with `--cpuset-cpus=0` (one core, no quota) and with `--cpus=4`. The bench measures the latency of 1000 requests, reads `cpu.max` and `cpu.stat` in the cgroup of the container, and times a background job that runs on 4 threads.

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `resume.py` = summary (turns the raw files into the outputs), `sorties/` = outputs. The outputs themselves are in English.

## How to replay

- Docker, for the `debian:bookworm-20261005` container in arm64 (pinned by digest in `rejouer.sh`). On x86_64, remove every `--platform linux/arm64` in `rejouer.sh`.
- `apt` in the container reads the Debian snapshot of 2026-10-14 (`https://snapshot.debian.org/archive/debian/20261014T000000Z/`), so the packages are the ones of that day: gcc `12.2.0`, glibc `2.36`, Python `3.11.2` (see `sorties/00-versions.txt`).
- Nothing to install on the host machine apart from Docker. `api.c` and `client.c` are compiled in the container; `resume.py` uses the Python standard library only.
- The host needs a cgroup v2 Docker (`docker info` shows `Cgroup Version: 2`) and at least 4 CPUs.

Single command (about 25 minutes on the machine of the article):

```bash
bash rejouer.sh
```

It compiles `bin/api` and `bin/client`, then for each of the four configurations runs the API container five times (`RUNS=5`), 20 s each, with the client in a second container on the same Docker network. Raw files go to `brut/` (not in the repo), the summaries to `sorties/01-cgroup.txt` to `sorties/04-job.txt`.

## The machine, and what changes from one run to the next

The outputs in this folder come from a Mac with Docker Desktop: the containers run in its Linux VM (linuxkit kernel, 10 CPUs, cgroup v2). Absolute latencies depend on that VM: a request of 1 ms of CPU has a median latency of about 4 ms even with no limit, and the bench does not measure where the rest goes (VM, Docker network). Other containers were running on the same VM during the measure. On another machine, expect other digits; the ratios between configurations are what the deck relies on.

What is stable: `sorties/00-versions.txt`, `sorties/01-cgroup.txt` (except the CPU list `0-9`, which is the number of CPUs of the VM), the CPU time of each request and job (counted with `CLOCK_THREAD_CPUTIME_ID`). What changes: latencies, wall times of the job, `throttled_usec`. Each output gives every run, then the median and the range.

## The model

- `api.c`: a TCP server on port 8080. Each request (`q\n`) costs 1 ms of CPU on the thread of its connection, then gets `ok\n`. Every second, a background job (think: cache refresh, garbage collection) runs on 4 threads, 50 ms of CPU each: 200 ms of CPU in one burst. For each job, `api` prints its wall time and its pauses (more than 2 ms of wall time with no job thread making progress).
- `client.c`: open-loop load: request k is due at `t0 + k x 20 ms` (50 requests per second), on 16 connections. Latency is counted from the due time, not from the moment the request was really sent, so a stall of the server cannot hide from the measure.
- Average CPU of the container: 1 ms x 50 + 200 ms = 0.25 CPU, with every configuration.

## File to slide

| File | Slide |
|---|---|
| `api.c`, `client.c` | 2 (the API, the background job, the load) |
| `sorties/01-cgroup.txt` | 3 (`cpu.max` and `cpuset.cpus.effective` for each `docker run` option) |
| `sorties/04-job.txt` | 4 (the job under `--cpus=1`: 25 ms of work, then a pause until the next period), 7 (one core with no quota) |
| `sorties/02-latency.txt` | 5 (p99 of the requests), 7 (comparison of the four configurations) |
| `sorties/03-cpustat.txt` | 6 (`nr_periods`, `nr_throttled`, `throttled_usec`) |
| `sorties/00-versions.txt` | versions of gcc, glibc and Python in the container |

## Third-party data

None. The bench downloads only the Debian image and the Debian packages above.
