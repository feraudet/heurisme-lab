# inodes-epuises

This bench goes with the deck https://heurisme.fr/en/blog/inodes-epuises/ : "No space left on device" while `df -h` still shows free space, because the filesystem has run out of inodes. A web server's `/var` is played by a 128 MiB ext4 image mounted through a loop device; PHP opens one session file per visitor until `session_start()` fails. Then: finding the folder that holds the inodes, who cleans PHP sessions on Debian, what `mke2fs -i` and `-N` change, and how XFS differs.

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `calcule.sh` = compute (runs in the container), `sessions.php` = the session loop, `sorties/` = outputs. In the outputs, `plein` = full, `coupable` = culprit, `options` = mkfs options. The outputs themselves are in English.

## How to replay

- Docker, for the `debian:bookworm-20261005` container in arm64 (pinned by digest in `rejouer.sh`). On x86_64, remove `--platform linux/arm64` in `rejouer.sh`.
- The container runs `--privileged`: it needs loop devices to mount the ext4 and XFS images. Everything happens inside the container (`/img`, `/srv/var`, `/mnt/xfs`); the images are deleted at the end.
- `apt` in the container reads the Debian snapshot of 2026-10-14 (`https://snapshot.debian.org/archive/debian/20261014T000000Z/` and `debian-security`), so the packages are the ones of that day: e2fsprogs `1.47.0-2+b2`, xfsprogs `6.1.0-1`, php8.2-cli `8.2.34-1~deb12u1` (see `sorties/00-versions.txt`).
- Nothing to install on the host machine apart from Docker.

Single command:

```bash
bash rejouer.sh
```

It takes about 15 seconds. Compare the outputs with the files provided: they come out byte for byte.

Two choices keep the outputs stable from one run to the next:

- `df` is called with `--output=...` and without the `Filesystem` column. The columns are the ones of `df -h` and `df -i`; the hidden column is the loop device (`/dev/loopN`), whose number depends on what else runs on the Docker VM.
- The XFS fill loop is pinned to one CPU (`taskset -c 0`). Unpinned, the number of files created before ENOSPC varies by multiples of 64 between runs (6460, 6524, 6588 seen on a 10-CPU VM); pinned, it is 6204 every time.

## The scenario

- `mkfs.ext4 -T default` on a 128 MiB image: below 512 MB, `mke2fs` would pick the `small` type (one inode per 4 KiB); `-T default` gives the ratio of a normal-size disk (one inode per 16 KiB, `inode_ratio = 16384` in `/etc/mke2fs.conf`): 8192 inodes. For comparison, a sparse 20 GiB image formatted without `-T` gets 1310720 inodes.
- The image is mounted on `/srv/var` and gets a 40 MB nginx-like log, 300 cache files, 40 queued mails, then `sessions.php` opens sessions (`session.save_path=/srv/var/lib/php/sessions`) until `session_start()` fails: 7830 sessions.
- `du --inodes` and `find | cut | sort | uniq -c` point at the sessions folder.
- The Debian PHP files show who cleans sessions: `session.gc_probability = 0` in `php.ini`, and `/usr/lib/php/sessionclean` run by `/etc/cron.d/php` or `phpsessionclean.timer`. The bench then deletes all sessions (a production cleanup keeps the `-cmin` age filter of `sessionclean`).
- `mkfs.ext4` again with `-i 4096` and `-N 20000`, then `resize2fs` from 128 to 256 MiB.
- XFS on a 300 MiB image: default `imaxpct`, then `-i maxpct=1`, filled with empty files until ENOSPC, then `xfs_growfs -m 5` on the mounted filesystem.

No real web server runs: nginx, cache and mail queue are plain files that stand for them. PHP is the real PHP CLI with the file session handler.

## File to slide

| File | Slide |
|---|---|
| `sorties/01-mkfs.txt` | 3 (inode ratio, 8192 inodes in 128 MiB, 1310720 in 20 GiB) |
| `sorties/02-plein.txt` | 4 (the PHP error, `df -h` at 72 %, inodes at 100 %, `touch` and `mkdir` fail, appending works) |
| `sorties/03-coupable.txt` | 5 (finding the folder) |
| `sorties/04-php.txt` | 2 (session folder), 6 (who cleans PHP sessions on Debian, cleanup) |
| `sorties/05-options.txt` | 7 (`-i`, `-N`, `resize2fs`) |
| `sorties/06-xfs.txt` | 8 (XFS `imaxpct`, `xfs_growfs -m`) |
| `sorties/00-versions.txt` | versions of the packages in the container |

## Third-party data

None. The bench downloads only Debian packages from snapshot.debian.org through `apt`.
