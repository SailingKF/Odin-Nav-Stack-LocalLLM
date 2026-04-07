# Current Round Prompt

## Round
Round 032 - WSL Enablement For MVSim And First Linux-Side Bring-Up

## Goal
Use WSL as the primary runtime-enablement route for MVSim on this PC: enable WSL, install a Linux distribution if needed, install or build the required MVSim/MRPT runtime there, and complete the first truthful Linux-side MVSim bring-up attempt using the repo’s minimal world.

## Why This Is The Current Priority

The previous retry round closed off the most obvious Windows-native routes:

- no package-manager path
- no usable native runtime already present
- Windows source-build path is blocked by MRPT dependency retrieval friction

That means the best next move is no longer “try Windows harder.” It is to switch to the more realistic Linux-side path through WSL.

This round should still stay narrow:

- first make WSL usable
- then make MVSim usable inside WSL
- then attempt the first Linux-side world bring-up

It should not yet expand into ROS, map-format work, or broad cross-OS architecture changes.

## In Scope

- determine whether WSL can be enabled on this PC in the current environment
- if WSL is not installed but can be installed, complete the narrowest viable install path
- install a practical Linux distribution for this use case if required
- verify Linux-side toolchain availability needed for MVSim/MRPT
- install or build MVSim/MRPT inside WSL using the most practical route found there
- verify a real Linux-side `mvsim` command exists
- use the existing repo-local world asset for the first truthful bring-up attempt
  - access via repo path sharing is acceptable
  - copying into WSL temporarily is acceptable if clearly documented
- attempt the first Linux-side launch of:
  - `mvsim launch <world-file>`
- if that succeeds, report the narrowest truthful next step toward bridging live pose into the current Windows-side tour path
- if that still fails, stop at the narrowest real blocker and report it precisely
- update docs/config/operator guidance only as needed to reflect the WSL path

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. WSL is enabled and a Linux-side `mvsim` runtime is runnable on this PC, with a first world-launch attempt completed.
2. WSL enablement or Linux-side runtime setup is blocked, but the blocker is now precisely identified.

What is not acceptable is staying in a generic “maybe WSL later” state.

## Out Of Scope

- ROS 2 formal adapter
- live pose bridge implementation into sim-ingress
- map-format or occupancy-map design
- autonomous navigation/path planning
- Isaac Sim
- Orin NX packaging
- simulator redesign
- TTS/ASR expansion

## Architecture Constraints

- keep `core` platform-agnostic
- do not rewrite the sim stack just to accommodate WSL
- treat WSL as a runtime-enablement environment, not as a reason to redesign service boundaries
- reuse the existing live probe, world asset, vehicle asset, and validation harness where possible
- keep any path/config changes explicit and minimal
- keep the bundle narrow and environment-focused

## Acceptance Criteria

- the round clearly determines whether WSL can be used for MVSim on this PC
- if WSL enablement succeeds, a real Linux-side `mvsim` command is verified
- the repo’s minimal world is used in a first Linux-side bring-up attempt
- exact commands and environment assumptions are documented
- operator/docs surfaces reflect the new truth about runtime availability
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- whether WSL was successfully enabled on this PC
- what Linux distribution/environment was used, if any
- whether `mvsim` became runnable inside WSL
- exact commands used for WSL setup, package install/build, and world bring-up
- whether the round ended in:
  - wsl_runtime_enabled
  - wsl_enabled_but_mvsim_blocked
  - wsl_install_blocked
- what happened when launching the repo-local world from WSL
- what the next narrow step is before implementing a live pose bridge
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not expand scope into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
