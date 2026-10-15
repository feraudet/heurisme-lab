#!/bin/bash
# Replays the IAM bench of the deck https://heurisme.fr/en/blog/policy-iam-evaluation/
# Needs Docker, an AWS account and the permission iam:SimulateCustomPolicy.
# Image debian:testing-20261005 pinned by digest, apt pointed at the Debian snapshot of 2026-10-14
# (the day before the article): awscli 2.36.17 and Python 3.
# The only network calls are apt and the IAM API (SimulateCustomPolicy, read only: nothing is created).
set -eu
cd "$(dirname "$0")"

# Credentials: taken from the environment if set, otherwise exported from an AWS CLI profile on the host.
# They are passed to the container by name (docker exec -e NAME), never printed.
if [ -z "${AWS_ACCESS_KEY_ID:-}" ]; then
  eval "$(aws configure export-credentials --profile "${AWS_PROFILE:-feraudet}" --format env)"
fi
export AWS_DEFAULT_REGION=eu-west-3

# Container: Debian testing arm64 (remove --platform on an x86_64 machine).
IMAGE=debian:testing-20261005@sha256:f35963177a0584848d5222b3d2b4f4ebcc6434d39db0a709c3088237ef619cbf
SNAP=20261014T000000Z
docker rm -f deck-policy-iam >/dev/null 2>&1 || true
docker run -d --name deck-policy-iam --platform linux/arm64 -v "$PWD":/w -w /w "$IMAGE" sleep infinity >/dev/null
docker exec deck-policy-iam bash -c "rm -f /etc/apt/sources.list.d/debian.sources && printf '%s\\n' \
  'deb http://snapshot.debian.org/archive/debian/$SNAP forky main' > /etc/apt/sources.list"
docker exec deck-policy-iam bash -c 'apt-get -o Acquire::Check-Valid-Until=false update -qq && apt-get install -y -qq awscli python3 >/dev/null'
mkdir -p sorties
docker exec deck-policy-iam bash -c 'dpkg-query -W awscli python3' > sorties/00-versions.txt

E="-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN -e AWS_DEFAULT_REGION"
docker exec $E deck-policy-iam python3 simule.py commands > sorties/commandes.txt
n=1
for g in default boundary deny scp; do
  docker exec $E deck-policy-iam python3 simule.py $g > sorties/0$n-$g.txt
  n=$((n + 1))
done

docker rm -f deck-policy-iam >/dev/null
echo "Outputs in sorties/. Compare with git diff."
