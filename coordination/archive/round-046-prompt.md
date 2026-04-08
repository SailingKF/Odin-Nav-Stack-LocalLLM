# Current Round Prompt

## Round
Round 046 - Ubuntu WSL Provisioning And MVSim Runtime Path Verification

## Goal
Now that the Windows-side WSL feature appears to be enabled on this PC, the next narrow goal is to finish the missing Ubuntu distribution step and verify whether the configured Linux-side MVSim runtime path can actually be reached from the current repo configuration.

This round is still an environment bring-up round.
It is not a product-feature round.

## Why This Is The Current Priority

Round 045 improved the repo-owned bootstrap path and removed the missing Python test dependency blocker.

Current owner-side machine truth after the user-installed reboot is now:

- `requirements-dev.txt` exists and the narrow harness-related tests were made reproducible
- `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml` no longer reports missing WSL
- instead, it reports:
  - `wsl_enablement.wsl_installed = true`
  - `effective_mode = "blocked_live_runtime"`
  - blocker code `wsl_mvsim_executable_not_found`
  - runtime check output: distro `Ubuntu` was not found
- `wsl.exe --status` now returns success and reports `默认版本: 2`
- the configured runtime contract still expects:
  - distribution: `Ubuntu`
  - user: `root`
  - executable path: `/root/round033-mvsim-build/bin/mvsim`

So the main risk is no longer Windows feature enablement.
The main risk is that the expected Ubuntu WSL environment and MVSim executable path may not yet exist on this machine.

## In Scope

- verify the current WSL distribution state truthfully
- install or initialize the expected Ubuntu distribution if it is still missing and if this can be done from the current session
- determine whether the configured distribution name should remain `Ubuntu` or be updated to the actual installed distro name
- verify whether `/root/round033-mvsim-build/bin/mvsim` exists inside the installed distro
- if that exact runtime path does not exist, take the narrowest truthful next step:
  - either document the missing-runtime blocker clearly
  - or re-run the already documented Ubuntu-side MVSim build path if it is feasible in this session
- update docs/config only as needed to keep the repo truthful and reproducible
- run the narrowest relevant validations and record the exact observed state

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. Ubuntu WSL exists on this PC and the configured MVSim runtime path is verified as present or updated truthfully.
2. Ubuntu WSL exists, but MVSim is still missing and the exact next Ubuntu-side command sequence is recorded clearly.
3. Ubuntu WSL still does not exist after attempted bring-up, and the exact blocker is recorded clearly.

Do not claim live MVSim readiness unless the configured distro and executable path were actually checked.

## Out Of Scope

- new harness UI work
- new map/reporting features
- broader simulator redesign
- Isaac Sim expansion
- Orin NX packaging
- unrelated product features
- broad dependency cleanup beyond what directly supports this round

## Architecture Constraints

- keep environment truth in docs, scripts, config, and coordination files
- do not push WSL-specific behavior into `core`
- do not add a heavyweight installer/orchestrator framework
- preserve the current `mvsim_integration` contract unless a truthful config correction is required
- prefer narrow config/doc corrections over speculative refactors

## Acceptance Criteria

- the current WSL distribution state is checked and recorded truthfully
- the round determines whether the expected distro name `Ubuntu` exists on this PC
- the round determines whether the configured MVSim path `/root/round033-mvsim-build/bin/mvsim` exists inside that distro
- if either the distro or executable is missing, the exact narrow blocker and next commands are recorded
- any needed config/doc changes are limited to making the repo truthful and reproducible

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- the exact current output summary of:
  - `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml`
  - `wsl.exe --status`
  - distro listing / verification command(s) used
  - runtime path verification command(s) used inside WSL
- whether the distro name `Ubuntu` existed, or what distro name was actually installed
- whether `/root/round033-mvsim-build/bin/mvsim` exists inside WSL
- whether any config field such as `wsl_distribution` or `wsl_executable_path` was updated
- whether this round ended in:
  - `ubuntu_wsl_ready_but_mvsim_missing`
  - `ubuntu_wsl_and_mvsim_path_verified`
  - `ubuntu_wsl_installation_still_blocked`
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If blocked, do not broaden into product work.
Finish the narrow WSL/distro/runtime verification bundle and stop.
