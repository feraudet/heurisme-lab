#!/bin/bash
# Runs inside the container: builds small ext4 and XFS images, fills them, writes sorties/.
# Each command is printed with "$ " before its output, then its exit status when it is not 0.
# df is called with --output and without the "Filesystem" column: the loop device number
# (/dev/loopN) depends on what else runs on the Docker VM, so it would change from run to run.
set -u
cd "$(dirname "$0")"
mkdir -p sorties /img /srv/var /mnt/xfs
umount /srv/var /mnt/xfs 2>/dev/null
rm -f /img/*.img

montre() {
  echo "\$ $1"
  ( cd /img && eval "$1" ) 2>&1
  local code=$?
  [ "$code" -ne 0 ] && echo "(exit $code)"
  echo
}
DFH='df -h --output=size,used,avail,pcent,target'
DFI='df --output=itotal,iused,iavail,ipcent,target'

# 01: a 128 MiB ext4 image with the inode ratio of a normal-size disk, mounted as /srv/var
{
  montre "grep -n 'inode_ratio' /etc/mke2fs.conf"
  montre 'truncate -s 128M var.img'
  montre 'mkfs.ext4 -q -T default var.img'
  montre "dumpe2fs -h var.img 2>/dev/null | grep -E '^(Block count|Block size|Inode count|Inode size):'"
  montre 'mount -o loop var.img /srv/var'
  montre "$DFH /srv/var"
  montre "$DFI /srv/var"
  montre 'truncate -s 20G disque-20G.img'
  montre 'mkfs.ext4 -q disque-20G.img'
  montre "dumpe2fs -h disque-20G.img 2>/dev/null | grep -E '^(Block count|Inode count):'"
  rm -f /img/disque-20G.img
} > sorties/01-mkfs.txt

# 02: the web server writes its log, its cache, its mail queue, then one PHP session per visitor
{
  montre 'mkdir -p /srv/var/log/nginx /srv/var/cache/nginx /srv/var/spool/postfix/deferred /srv/var/lib/php/sessions'
  montre "yes 'GET /panier HTTP/1.1 200' | head -c 40M > /srv/var/log/nginx/access.log"
  montre 'for n in $(seq 1 300); do head -c 3000 /dev/zero > /srv/var/cache/nginx/c$n; done'
  montre 'for n in $(seq 1 40); do echo "message $n" > /srv/var/spool/postfix/deferred/m$n; done'
  montre 'php -d session.save_path=/srv/var/lib/php/sessions -d session.use_cookies=0 /w/sessions.php'
  montre "$DFH /srv/var"
  montre "$DFI /srv/var"
  montre 'touch /srv/var/log/nginx/error.log'
  montre 'mkdir /srv/var/cache/nginx/tmp'
  montre "echo 'GET / HTTP/1.1 200' >> /srv/var/log/nginx/access.log && echo appended"
} > sorties/02-plein.txt

# 03: finding the folder that holds the inodes
{
  montre 'du --inodes -x -d 3 /srv/var | sort -n | tail -5'
  montre 'find /srv/var -xdev -type f | cut -d/ -f1-5 | sort | uniq -c | sort -n'
} > sorties/03-coupable.txt

# 04: who is supposed to clean PHP sessions on Debian, then the cleanup
{
  montre "php -r 'echo ini_get(\"session.save_path\"), PHP_EOL;'"
  montre "grep -n '^session.gc' /etc/php/8.2/cli/php.ini"
  montre "grep -v '^#' /etc/cron.d/php | grep ."
  montre 'grep -E "^(OnCalendar|OnBootSec)" /lib/systemd/system/phpsessionclean.timer'
  montre "grep -n -- '-cmin' /usr/lib/php/sessionclean"
  montre "find /srv/var/lib/php/sessions -name 'sess_*' -type f -delete"
  montre "$DFI /srv/var"
  montre 'touch /srv/var/log/nginx/error.log && echo created'
} > sorties/04-php.txt
umount /srv/var

# 05: what mkfs options change, and what can still change afterwards
{
  for opts in '' '-i 4096' '-N 20000'; do
    montre 'rm -f essai.img && truncate -s 128M essai.img'
    montre "mkfs.ext4 -q -T default ${opts:+$opts }essai.img"
    montre "dumpe2fs -h essai.img 2>/dev/null | grep -E '^(Inode count|Free blocks):'"
  done
  montre 'mkfs.ext4 -q -T default essai.img'
  montre 'truncate -s 256M essai.img && resize2fs essai.img'
  montre "dumpe2fs -h essai.img 2>/dev/null | grep -E '^(Block count|Inode count):'"
  rm -f /img/essai.img
} > sorties/05-options.txt

# 06: XFS allocates inodes when files are created, up to imaxpct of the space.
# The fill loop is pinned to CPU 0: unpinned, the count varies by multiples of 64 from run to run.
{
  montre 'truncate -s 300M xfs.img'
  montre 'mkfs.xfs -q xfs.img'
  montre 'mount -o loop xfs.img /mnt/xfs'
  montre "xfs_info /mnt/xfs | grep -o 'imaxpct=[0-9]*'"
  montre "$DFI /mnt/xfs"
  montre 'umount /mnt/xfs'
  montre 'mkfs.xfs -q -f -i maxpct=1 xfs.img'
  montre 'mount -o loop xfs.img /mnt/xfs'
  montre "$DFI /mnt/xfs"
  montre 'mkdir /mnt/xfs/s; taskset -c 0 bash -c '\''n=0; while touch /mnt/xfs/s/f$n; do n=$((n+1)); done; echo "$n files created"'\'''
  montre "$DFH /mnt/xfs"
  montre "$DFI /mnt/xfs"
  montre 'xfs_growfs -m 5 /mnt/xfs | tail -1'
  montre 'touch /mnt/xfs/s/after && echo created'
  montre "$DFI /mnt/xfs"
  montre 'umount /mnt/xfs'
} > sorties/06-xfs.txt
rm -f /img/*.img
