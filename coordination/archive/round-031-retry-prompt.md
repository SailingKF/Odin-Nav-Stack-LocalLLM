# Current Round Prompt

## Round
Round 031 Retry - MVSim Runtime Enablement And First Live Bring-Up

## Goal
Close the current environment blocker by getting a real local `mvsim` runtime installed, discoverable, and usable on this PC, then complete the first true live-runtime bring-up attempt against the repo’s minimal MVSim world.

## Why This Is The Current Priority

The architecture is no longer the main unknown.

Round 031 already established:

- a minimal repo-local MVSim world and vehicle asset
- live-runtime probing
- operator-visible distinction between live mode and compatibility mode
- truthful blocker handling when no runtime exists

The remaining first-order blocker is external and concrete:

- this PC does not currently have a usable `mvsim` executable

So the next round should not invent more simulation abstractions.
It should focus on enabling the environment and then immediately using that environment to attempt the first real live bring-up.

## In Scope

- determine the most practical way to install or make `mvsim` available on this Windows PC
- if installation is possible within the current environment, complete it
- verify runtime discovery with real commands, not assumptions
- update config only as needed so the repo points at the actual executable path or command shape
- use the existing repo-local world asset:
  - `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`
- use the existing repo-local vehicle asset:
  - `content/sim/mvsim/definitions/odin_tour_bot.vehicle.xml`
- attempt the first true live-runtime bring-up
- if live bring-up succeeds, validate the narrowest truthful next step toward feeding live pose into the current stack
- if live bring-up still fails, stop at the narrowest real blocker and report it precisely
- update the validation harness/operator surfaces if needed so they reflect the real runtime availability after installation

## Desired Outcome

At the end of this round, the project should be in one of these two honest states:

1. `mvsim` is installed and discoverable on this PC, and the first live bring-up has been attempted with exact observed results.
2. `mvsim` still cannot be enabled on this PC, but the exact installation/runtime blocker is now concretely identified.

What is not acceptable is remaining in a vague “runtime missing” state without pushing the environment question forward.

## Out Of Scope

- ROS 2 formal adapter
- simulator architecture redesign
- map-format or occupancy-map design
- autonomous navigation/path planning
- Isaac Sim
- Orin NX packaging
- broad UI redesign
- TTS/ASR expansion

## Architecture Constraints

- keep `core` platform-agnostic
- do not rewrite sim-ingress or orchestrator just to chase runtime installation
- reuse the existing live probe, world asset, vehicle asset, and validation harness
- keep all simulator-specific logic in adapters/services/docs/scripts
- if config must change for executable discovery, keep it explicit and minimal
- keep the bundle narrow and environment-focused

## Acceptance Criteria

- the round clearly determines whether a usable `mvsim` runtime can exist on this PC
- runtime discovery is verified with exact commands/results
- if installation succeeds, the repo can point to the real executable path or command
- the first live world bring-up is attempted with exact observed results
- operator surfaces/docs reflect the new truth about runtime availability
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- whether `mvsim` was successfully installed or enabled on this PC
- exact commands used for install/discovery/bring-up
- what executable path or command now works, if any
- whether the round ended in:
  - live_runtime_enabled
  - live_runtime_attempted_but_blocked
  - install_blocked
- what happened when launching the repo-local world
- whether the harness now reports live runtime available
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before the next live pose bridge step

If you hit a blocker, do not expand scope into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
