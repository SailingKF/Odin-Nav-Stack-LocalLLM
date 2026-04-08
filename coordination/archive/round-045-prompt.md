# Current Round Prompt

## Round
Round 045 - Local Environment Bootstrap And WSL MVSim Readiness Baseline

## Goal
The next narrow goal is to make the current PC-side simulation environment reproducible enough that a developer can truthfully prepare for live MVSim validation on this Windows machine without relying on hidden setup history.

This round is not about adding another product feature.
It is about turning the current environment assumptions into a repo-owned bootstrap path.

## Why This Is The Current Priority

Round 044 appears to have closed the current report-only map fallback gap.

Current owner-side repo and machine truth is now:

- `main` is clean and aligned with local `origin/main`
- focused MVSim reporting and map-view tests pass on this machine
- `tests.test_mvsim_validation_harness` is currently blocked locally because `httpx` is not installed
- `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml` currently reports:
  - `configured_mode = "live_runtime"`
  - `effective_mode = "blocked_live_runtime"`
  - blocker: WSL is not installed or not ready on this PC
- `wsl.exe --status` currently reports that WSL for Linux is not installed on this Windows machine

That means the main risk is no longer the harness map.
The main risk is that the current dev/sim environment is not yet reproducible from the repository alone.

## In Scope

- add an explicit Python dependency manifest for the current repo-owned dev/test path if one is still missing
- make the current harness/API test dependency path reproducible on a fresh Windows dev machine
- make the WSL + Ubuntu + Linux-side MVSim bring-up path repo-owned and easy to follow
- distinguish clearly between:
  - steps that can run in a normal shell
  - steps that require an elevated Windows shell
  - steps that must run inside Ubuntu on WSL
- prefer improving existing docs/scripts over introducing a new orchestration service
- update existing docs for live MVSim bring-up and harness usage as needed
- add or improve one lightweight repo-owned probe / helper script only if it materially reduces ambiguity
- run the narrowest truthful validations available in the current session

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. A fresh developer on Windows can install the current Python dependencies, understand the exact WSL/MVSim bring-up sequence, and reproduce the next steps without hidden knowledge.
2. The environment bootstrap is partially improved, but the exact remaining blocker is explicit and narrow.

If the current shell cannot complete the admin-required WSL install, do not pretend the live runtime is enabled.
Stop at the narrowest truthful blocker after finishing all non-admin repo work.

## Out Of Scope

- new harness map features
- simulator-side UI
- broader `/debug` redesign
- ROS 2 formal adapter work
- Isaac Sim expansion
- Orin NX packaging work
- broader deployment automation beyond the narrow Windows/WSL/MVSim bootstrap path
- new narration, route, or analytics features

## Architecture Constraints

- keep environment/bootstrap concerns in docs, scripts, and validation seams
- do not push environment-specific setup logic into `core`
- do not add a heavyweight installer framework
- prefer one clear source of truth over scattered setup snippets
- preserve the current harness/runtime boundaries
- keep the result honest about what was truly validated on this machine

## Acceptance Criteria

- the repo has an explicit Python dependency entry point for current dev/test usage, or the exact reason for not adding one is stated clearly
- the current machine can install or at least verify the missing harness/test dependency path from repo-owned instructions
- the repo documents the exact Windows-elevated WSL enablement step and the exact Ubuntu-side MVSim setup path
- the repo documents how to validate:
  - Python test readiness
  - WSL readiness
  - configured MVSim live-runtime readiness
- the programmer thread runs the narrowest truthful validations available and reports the exact observed machine state

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- whether a Python dependency manifest was added or updated
- the exact install command(s) now recommended for this repo
- which step(s) require elevation on Windows
- which step(s) must run inside WSL Ubuntu
- the exact current result of:
  - `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml`
  - the harness-related test command(s) you ran
  - `wsl.exe --status` if attempted
- whether this round ended in:
  - `environment_bootstrap_documented`
  - `environment_bootstrap_partially_enabled`
  - `environment_bootstrap_blocked_on_elevation`
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If blocked, do not broaden into simulator redesign or new app features.
Finish the bootstrap/documentation/dependency bundle and record the narrow blocker clearly.
