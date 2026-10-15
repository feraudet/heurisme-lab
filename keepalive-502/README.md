# keepalive-502

This bench goes with the deck https://heurisme.fr/en/blog/keepalive-502/ : rare, random 502 errors behind a reverse proxy or a load balancer. Node.js closes an idle keep-alive connection after 5 s (its default), nginx keeps it in its cache for 60 s (its default). When a request leaves nginx at the very moment Node.js closes the connection, nginx answers 502. The bench counts these 502s, reads the nginx error log, then makes the count fall to zero in two ways: a longer timeout on the Node.js side, or a shorter one on the nginx side.

File names are in French where the original article is: `rejouer.sh` = replay script, `calcule.sh` = compute (runs in the container), `sorties/` = outputs. The scripts and the outputs themselves are in English.

## How to replay

- Docker, for the `debian:bookworm-20261005` container in arm64 (pinned by digest in `rejouer.sh`). On x86_64, remove `--platform linux/arm64` in `rejouer.sh`.
- `apt` in the container reads the Debian snapshot of 2026-10-14 (`https://snapshot.debian.org/archive/debian/20261014T000000Z/` and the matching `debian-security`), so the packages are the ones of that day: nginx-light `1.22.1-9+deb12u10`, nodejs `18.20.4+dfsg-1~deb12u3`, python3 `3.11.2-1+b1` (see `sorties/00-versions.txt`).
- Nothing to install on the host machine apart from Docker. No npm or pip package: Node.js and Python standard libraries only.

Single command (about 30 minutes):

```bash
bash rejouer.sh
```

## How it works

- `backend.js`: the API, a plain `http.createServer` that answers `200 ok` to anything. It listens on 20 ports (3000 to 3019). Its first argument is `server.keepAliveTimeout` in ms, or `default` to keep the Node.js default (5000 ms).
- `nginx_conf.py`: writes the nginx configuration. 20 lanes: nginx port 8000 + n in front of Node.js port 3000 + n, each with its own `upstream` block (`keepalive 4`, `keepalive_timeout` from the first argument) and `proxy_http_version 1.1` with `proxy_set_header Connection ""`. nginx 1.22 needs these three lines to reuse upstream connections.
- `client.py`: on each lane, one request, then a pause (the gap), then the next request, and so on. The gaps are 3000 ms, every 2 ms from 4980 to 5020 ms, then 7000 ms: 23 gaps, so 460 requests per run over the 20 lanes. The gap is measured from the end of the previous response.
- `scenario.py`: starts Node.js and nginx, runs the client, stops both, then groups the nginx error log by message (date, pid, connection number and port removed, the message is kept as is) and the access log by `$request_method $status upstream=$upstream_status`. It repeats this for several runs and prints the 502 count of each run, the median, the min and the max.
- `calcule.sh`: the four scenarios.

## The outputs change from run to run

The 502s come from a race of a few milliseconds between nginx sending a request and Node.js closing the connection. The count changes on every run, even on the same machine; the outputs give each run and the median. What does not change: no 502 at 3000 ms or 7000 ms of gap, no 502 for GET requests (nginx retries them, `upstream=502, 200`), and no 502 at all once nginx closes first.

## File to slide

| File | Slide |
|---|---|
| `sorties/01-post-5s-60s.txt` | 4 (502 count per gap, run 1, and the 5 runs), 5 (error log messages), 7 (the original setting) |
| `sorties/02-get-5s-60s.txt` | 6 (GET: nginx retries, `upstream=502, 200`) |
| `sorties/03-post-65s-60s.txt` | 7 (fix on the API: `keepAliveTimeout` 65 s) |
| `sorties/04-post-5s-4s.txt` | 7 (fix on the proxy: `keepalive_timeout 4s`) |
| `sorties/00-versions.txt` | versions of nginx, Node.js and Python in the container |

## Third-party data

None. The bench only uses Debian packages and the scripts of this folder. The run files (`run/`: nginx configuration and logs) are rewritten on each run and are not in the repo.
