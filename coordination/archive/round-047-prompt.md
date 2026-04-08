# Current Round Prompt

## Round
Round 047 - Live MVSim Pose Flow And Harness End-To-End Validation

## Goal
Now that the configured WSL runtime path is verified, the next narrow goal is to prove whether live MVSim pose can actually flow end-to-end through the current bridge and isolated harness stack on this PC.

This round is a validation-flow round.
It is not a new feature round.

## Why This Is The Current Priority

Round 046 closed the runtime-availability question:

- `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml` now reports `effective_mode = "live_runtime"`
- the configured distro `Ubuntu` exists
- the configured executable `/root/round033-mvsim-build/bin/mvsim` exists and responds

That means the main remaining risk is no longer WSL install or runtime path configuration.
The main remaining risk is whether the current repo can still move truthful live pose from:

1. WSL MVSim runtime
2. into the live bridge path
3. into the isolated sim ingress + API stack
4. into the validation harness and route/progression truth

If this does not work end-to-end, the next blocker needs to be recorded at the exact failing seam.

## In Scope

- use the existing repo-owned live validation path to verify the current end-to-end live pose flow on this PC
- prefer the highest-signal existing seam:
  - `scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml`
- if the full harness flow is blocked, use the narrower existing live bridge seam to isolate the blocker:
  - `scripts/run_mvsim_live_bridge_demo.py`
- verify whether live pose reaches the isolated local services truthfully
- verify whether the current live validation run can truthfully report:
  - live runtime used
  - live pose relay used
  - first live stop hit
  - second live stop hit
  - route completion
- update docs only if current machine-truth or run instructions are now stale
- make only the smallest code changes needed to restore the current live validation seam if a narrow bug is found

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. The isolated harness can complete a truthful live MVSim validation run on this PC, including live pose flow and route progression evidence.
2. Live pose reaches part of the stack, but the exact next failing seam is explicit.
3. The live path is blocked earlier, and the exact blocker is explicit with matching evidence.

Do not claim success based only on runtime availability.
Success requires end-to-end live validation evidence or a clearly isolated blocker.

## Out Of Scope

- new UI features
- broader harness redesign
- new map/reporting features unless they directly block truthful validation evidence
- Isaac Sim expansion
- Orin NX deployment work
- broad refactors
- unrelated product functionality

## Architecture Constraints

- preserve the current split between runtime probe, live bridge, sim ingress, API service, and harness
- do not push simulator-specific behavior into `core`
- prefer validating the existing seams over inventing a new supervisor path
- if a bug is found, fix only the narrow seam required for truthful live validation
- keep docs/result files honest about what was actually observed on this PC

## Acceptance Criteria

- the round runs the current live validation path or isolates the narrowest blocker with existing live bridge tooling
- the round determines whether live pose from WSL MVSim reaches the repo-owned isolated stack
- the round determines whether the harness can truthfully show a live validation result on this PC
- if route progression is reached, the result states whether first stop, second stop, and route completion were actually seen
- if blocked, the exact seam and blocker are recorded with real command evidence

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- which validation path you used:
  - full harness
  - live bridge seam
  - both
- the exact commands used
- the exact observed result of:
  - `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml`
  - live bridge command(s)
  - harness run / API calls / status checks used
- whether the validation truthfully used:
  - WSL live runtime
  - live pose relay
  - isolated harness stack
- whether the run truthfully saw:
  - first live stop hit
  - second live stop hit
  - route completion
- whether persisted report artifacts were written and what key facts they contained
- whether this round ended in:
  - `live_mvsim_end_to_end_verified`
  - `live_mvsim_pose_flow_partially_verified`
  - `live_mvsim_flow_blocked`
- what the next narrow step is after this
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If blocked, do not broaden into product work.
Stop at the narrowest live-validation blocker and record it clearly.
