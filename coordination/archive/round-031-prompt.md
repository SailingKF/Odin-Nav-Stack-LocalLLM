# Current Round Prompt

## Round
Round 031 - MVSim Live Runtime And Minimal World Bring-Up Baseline

## Goal
Move the MVSim path from compatibility-playback-first toward a real live simulator bring-up on PC by running an actual `mvsim` process with a minimal world and driving the existing tour stack from live simulator pose output.

## Why This Is The Current Priority

Rounds 029 and 030 already proved two things:

- the downstream tour chain works with an MVSim-oriented compatibility path
- the operator now has a practical human validation harness

That means the next highest-value unknown is no longer operator UX. It is whether a real local MVSim runtime can be brought up and connected to the existing simulation path without forcing ROS or a large simulation redesign.

For this project, “more complete simulation” at this stage means:

- real `mvsim` process
- real minimal world file
- live simulator pose entering the current stack
- existing route / POI / narration / session / debug flow still working

It does **not** mean:

- full navigation stack
- complex sensors
- ROS formalization
- high-fidelity quadruped dynamics

## In Scope

- detect and use a real local `mvsim` runtime if available on this PC
- add a minimal MVSim world asset suitable for this project’s current needs
  - a simple wheeled/mobile robot is acceptable
  - do not optimize for quadruped realism
- add a narrow live MVSim adapter or bridge path that turns live simulator output into the existing sim-ingress-compatible flow
- preserve the existing compatibility shim path unless there is a very strong reason to remove it
- make the distinction between:
  - `live_mvsim_runtime`
  - `mvsim_compatibility_shim`
  explicit in operator-facing output where practical
- validate one full live-simulator-driven tour on PC if the real runtime is available
- if the runtime is not available, fail narrowly and report exactly what is missing rather than faking success
- update the current validation harness so an operator can clearly see whether they are running:
  - live MVSim mode
  - compatibility mode
- add focused docs and tests for the live runtime path where practical

## Desired Outcome

After this round, the repo should be able to answer one concrete question:

“Can a real MVSim world running on this PC drive the current tour system end-to-end?”

The answer can be:

- yes, and here is the exact validated flow
- or no, because this specific runtime/dependency/world blocker still exists

But it should no longer stay ambiguous.

## Out Of Scope

- ROS 2 formal adapter
- Isaac Sim
- map-format or occupancy-map architecture
- autonomous navigation or path planning
- sensor simulation beyond what is minimally needed for pose extraction
- real hardware integration
- Orin NX packaging
- generic simulator framework refactors
- TTS/ASR expansion

## Architecture Constraints

- keep `core` platform-agnostic
- keep simulator-specific logic in adapters/services, not in orchestrator/core
- do not rewrite the current sim-ingress contract unless absolutely necessary
- prefer a narrow live-runtime seam over a broad new abstraction layer
- preserve the current validation harness and `/debug` path
- if live runtime support requires additional config, keep it minimal and explicit
- keep the bundle coherent and narrow

## Acceptance Criteria

- repository contains a clear live MVSim runtime bring-up path or a narrowly reported real blocker
- a minimal world asset exists for project use
- live and compatibility modes are clearly distinguished in code/docs/operator surfaces
- if `mvsim` is available, one full live-simulator-driven validation is demonstrated through the existing stack
- if `mvsim` is not available, the result explicitly reports the real blocker and stops there
- focused tests pass
- existing related tests still pass
- docs clearly explain how to run the live path and how to tell which mode is active

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- whether a real `mvsim` runtime was found on this PC
- whether the round completed in live mode, compatibility mode fallback, or blocker state
- what minimal world asset now exists
- how live simulator pose is turned into the existing tour path
- how the harness/operator can tell live vs compatibility mode
- exact validation performed
- exact commands used
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before map-format or ROS work

If you hit a blocker, do not expand scope into ROS, map-format design, or simulator redesign.
Stop at the narrowest real blocker and describe it clearly.
