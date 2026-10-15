# policy-iam-evaluation

This bench goes with the deck https://heurisme.fr/en/blog/policy-iam-evaluation/ : why an `Allow` is not enough in AWS IAM. A deploy role is allowed `s3:PutObject` on `releases/*` of a bucket, and the IAM policy simulator is asked the same question again and again while policies are added one layer at a time: identity policy, permissions boundary, bucket policy with an explicit `Deny` on a condition (`aws:SecureTransport`), then service control policies (SCPs) of an organization, one of them denying any region but `eu-west-3` (`aws:RequestedRegion`).

File names are in French because the original article is. Useful names: `rejouer.sh` = replay script, `simule.py` = simulate (runs in the container), `sorties/` = outputs, `brut/` = raw JSON answers (not kept in git). The outputs themselves are in English.

## What you need

- **An AWS account** and credentials allowed to call **`iam:SimulateCustomPolicy`**. The bench only calls `SimulateCustomPolicy`, a read-only API: it creates nothing, sends no request to S3 and needs no bucket. The bucket `amzn-s3-demo-bucket`, the role `arn:aws:iam::111122223333:role/deploy` and the account `111122223333` are the example names of the AWS documentation; your own account number is never printed.
- Docker, for the `debian:testing-20261005` container in arm64 (pinned by digest in `rejouer.sh`). On x86_64, remove `--platform linux/arm64` in `rejouer.sh`.
- `apt` in the container reads the Debian snapshot of 2026-10-14 (`https://snapshot.debian.org/archive/debian/20261014T000000Z/`, suite `forky`), so the packages are the ones of that day: awscli `2.36.17`, Python 3 (see `sorties/00-versions.txt`). AWS CLI 2.36.12 and later have `--ordered-organization-policy-input-list`, used for the SCPs.
- Credentials: if `AWS_ACCESS_KEY_ID` is set, it is used; otherwise `rejouer.sh` runs `aws configure export-credentials --profile $AWS_PROFILE` on the host (default profile name: `feraudet`, set `AWS_PROFILE` to yours). The variables are passed to the container by name, never printed.

Single command:

```bash
AWS_PROFILE=<your-profile> bash rejouer.sh
```

It recreates the container, writes `sorties/commandes.txt` (the exact `aws iam simulate-custom-policy` command of each case), then `sorties/01-default.txt` to `sorties/04-scp.txt`. Compare with the files provided with `git diff`: they come out byte for byte as long as the IAM API answers the same way. The simulator is a live AWS service; AWS has already changed its answers (one result per action, SCP conditions evaluated), so a later replay may differ.

## What the outputs keep

`simule.py` keeps, for each case: `EvalDecision`, `MatchedStatements` (policy id, type and line range of the statement), `MissingContextValues`, and, when the API returns them, `PermissionsBoundaryDecisionDetail.AllowedByPermissionsBoundary` and `OrganizationsDecisionDetail.AllowedByOrganizations`. Lists are sorted, so the output is stable.

## The cases

| Case | Identity policy | Boundary | Bucket policy | SCPs (root > account) | Context |
|---|---|---|---|---|---|
| A | `role-lecture.json` (GetObject only) | | | | |
| B | `role-deploy.json` (PutObject on `releases/*`) | | | | |
| C | `role-deploy.json` | `boundary-lecture.json` (read only) | | | |
| D | `role-deploy.json` | `boundary-deploy.json` (read and write) | | | |
| E | `role-deploy.json` | `boundary-deploy.json` | `bucket-https.json` (Deny if `aws:SecureTransport` is false) | | `aws:SecureTransport=false` |
| F | same | same | same | | `aws:SecureTransport=true` |
| G | same | same | same | | none |
| H | `role-deploy.json` | `boundary-deploy.json` | | `scp-full-access` > `scp-ec2-only` | |
| I | `role-deploy.json` | `boundary-deploy.json` | | `scp-full-access` > `scp-full-access` + `scp-region` | `aws:RequestedRegion=us-east-1` |
| J | same | same | | same | none |
| K | same | same | | same | `aws:RequestedRegion=eu-west-3` |

`policies/org-*.json` are written by `simule.py` from the `scp-*.json` files (the API wants each SCP as a JSON string).

## What the bench does not simulate

- Resource control policies (RCPs): the simulator does not support them (IAM User Guide, "IAM policy testing with the IAM policy simulator").
- Session policies passed to `AssumeRole`: `SimulateCustomPolicy` does not take scope-down policies (API reference, `PolicyInputList`).
- The real request: the simulator answers from the policies it is given. AWS says its results can differ from the live environment.

## File to slide

| File | Slide |
|---|---|
| `sorties/01-default.txt` | 3 (implicit deny by default) |
| `sorties/02-boundary.txt` | 4 (permissions boundary) |
| `sorties/03-deny.txt` | 5 (explicit deny with `aws:SecureTransport`) |
| `sorties/04-scp.txt` | 6 (SCPs), 7 (where each case stops) |
| `sorties/commandes.txt` | the exact `aws` commands |
| `policies/*.json` | the policies of every case |
| `sorties/00-versions.txt` | versions of awscli and Python in the container |

## Third-party data

None. The policies are written for this bench; the evaluation rules come from the AWS documentation cited in the deck.
