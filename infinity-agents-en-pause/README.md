# Infinity bench: 80,000 agents paused while their tools run

This bench goes with the article https://heurisme.fr/en/blog/infinity-agents-en-pause/ : the memory benchmark of Infinity, the agent runtime from AWS and UC Berkeley (Hydro project, Apache 2.0, https://github.com/hydro-project/infinity), replayed and extended with two measurements of ours. No real LLM, no AWS account, no key: Infinity's own scripted model (about 1.2 KB of text per completion, one tool call per turn) and in-memory stores.

File names and outputs are in French because the original article is. Useful names: `rejouer.sh` = replay script, `raw/` = raw outputs, `analyse.py` = analysis, `synthese.txt` = summary, `naive` = naive, `pending` = waiting on a tool, `limites_noyau.txt` = kernel limits. The summary `raw/synthese.txt` is in French.

## How to replay

Docker. Image `rust:1.90-bookworm`, pinned by digest `sha256:3914072ca0c3b8aad871db9169a651ccfce30cf58303e5d6f2db16d1d8a7e58f`. Inside: rustc 1.90.0, linux/arm64. Infinity cloned at commit `341f6c2` (2026-10-23). The benchmark reads `/proc/self/status`, so it only runs on Linux, hence the container.

Four modes:

- `bash rejouer.sh infinity`: Infinity's own example `agent_scale`, unchanged. Agents idle between turns.
- `bash rejouer.sh pending`: our variant `patches/agent_scale_pending.rs`, copied into Infinity's examples for the run then removed. Same benchmark, plus one last tool call that never answers: RSS is sampled while every agent waits on a tool.
- `bash rejouer.sh naive`: our naive model in `naive/` (not Infinity). Each agent owns a history of the same shape and waits for a tool result that never comes, three ways: `none` (history in a Vec, nothing waits), `task` (a tokio task awaits a oneshot), `thread` (an OS thread blocks on a channel).
- `bash rejouer.sh all`, then `python3 analyse.py` writes `raw/synthese.txt`.

Environment variables: `AGENTS` (default 10000), `TURNS` (20), `WAVE` (500). We used `AGENTS=80000` for `infinity` and `naive`, and `AGENTS=50000` for `pending`. 80,000 agents take about 5 minutes for `infinity` on a Mac M4 Max with Docker.

Watch the memory of the Docker VM. Ours has 16 GB and 4 GB of swap. A first `pending` run with 80,000 agents swapped from 60,000 agents on, and its RSS flattened: it is kept as `raw/pending_80000x20_swap.csv` but not used. The `pending` run with 50,000 agents peaks at 10.5 GiB and stays linear.

## Why waiting costs more than idle

In Infinity's local driver (`crates/infinity-agent-core/src/system/local/driver.rs`, `check_before_idle`, lines 331-363, `AwaitInput` at line 357), a thread still awaiting a tool result returns `IdleDecision::AwaitInput` and its driver stays resident. It only exits when nothing is expected. The driver holds a `Thread`, which holds a `HistoryManager` with `history: RefCell<Vec<InfinityMessage>>` and `processed_message_ids` (`event_processor.rs`, lines 147-148): a loaded copy of the history on top of the in-memory store.

On Lambda the process exits after each step and the history lives in Aurora DSQL, so this local cost does not apply there.

## Results

Per-agent cost = slope of RSS between 10,000 agents and the last sample.

- `infinity`: 80,000 agents, 20 turns each, 3,200,000 completions, 274.1 s, 99.1 KiB per idle agent. AWS announces about 100 KB. At 75,000 agents: 7.13 GiB.
- `pending` (50,000 agents): 220.0 KiB per agent waiting on a tool, 2.2 times an idle agent, 120.9 KiB more. That extra cost is larger than the stored history itself, so the loaded copy does not explain all of it; the rest was not broken down. At 75,000 agents, extrapolated: 15.74 GiB.
- `naive` at 65,000 agents, compared with `none`: `task` adds 352 bytes of RSS per agent; `thread` adds 10,458 bytes of RSS and 2.16 MiB of virtual memory per agent.
- `thread` stops after 65,000 threads: each Rust thread takes about 4 memory mappings (40,181 for 10,000 threads), the container kernel allows `vm.max_map_count` = 262,144, and at 65,000 threads the process has 260,181. The next thread panics with "failed to allocate an alternative stack: Cannot allocate memory (os error 12)".

## What is not measured

No real model latency, no Aurora DSQL or DynamoDB latency, no Lambda deployment, not a Raspberry Pi (the 8 GB Pi 5 is a reference line in AWS's figure; AWS ran on one thread of an AMD EPYC 9R14).

## File to slide

| File | Slide |
|---|---|
| `raw/infinity_80000x20.csv`, `.log` | 6 |
| `raw/pending_50000x20.csv`, `.log` | 7 |
| `raw/pending_80000x20_swap.csv`, `.log` | not used (swap) |
| `raw/naive_*_80000x20.csv`, `.log`, `raw/limites_noyau.txt` | 8 |
| `raw/synthese.txt` | 6 to 8 |
| `raw/infinity_1000x20.*` | first smoke run with 1,000 agents |

## Sources

| What | Link |
|---|---|
| AWS blog post "Introducing Infinity: a runtime for extreme agent concurrency", Shadaj Laddad, 2026-10-23 | https://aws.amazon.com/blogs/opensource/introducing-infinity-a-runtime-for-extreme-agent-concurrency/ |
| Infinity docs | https://infinity.hydro.run |
| Infinity repo at commit `341f6c2` | https://github.com/hydro-project/infinity |
| Benchmark | `crates/infinity-agent-core/examples/agent_scale.rs` |

## Third-party code

Infinity is not copied into this repo; `rejouer.sh` clones it into `src/` (ignored). `patches/agent_scale_pending.rs` is derived from Infinity's `agent_scale.rs` (Apache 2.0), modified as stated in its header.
