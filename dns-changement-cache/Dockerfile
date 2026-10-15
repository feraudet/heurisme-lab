# One image for the three containers of the bench: the authoritative server (NSD),
# the recursive resolver (Unbound) and the client (dig).
# Debian 12 pinned by digest, apt pointed at the Debian snapshot of 2026-10-14.
FROM debian:bookworm-20261005@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858
ARG SNAP=20261014T000000Z
RUN rm -f /etc/apt/sources.list.d/debian.sources \
 && echo "deb http://snapshot.debian.org/archive/debian/$SNAP bookworm main" > /etc/apt/sources.list \
 && apt-get -o Acquire::Check-Valid-Until=false update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends nsd unbound bind9-dnsutils procps >/dev/null \
 && rm -rf /var/lib/apt/lists/*
