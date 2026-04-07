# Current Round Prompt

## Round
Round 033 - WSL MVSim Runtime Install And First Linux-Side World Launch

## Goal
Now that WSL2 + Ubuntu are confirmed available on this PC, install or build the required MVSim/MRPT runtime inside Ubuntu and complete the first truthful Linux-side launch attempt of the repo’s minimal MVSim world.

## Why This Is The Current Priority

The previous round was about environment enablement, and that blocker has now materially changed outside the repo:

- WSL is available
- Ubuntu exists
- Ubuntu is running under WSL2

That means the next highest-value unknown is no longer “can we use WSL?”
It is:

- can `mvsim` be made runnable inside Ubuntu on this machine
- and can the repo’s minimal world actually launch there

This round should stay narrow and honest:

- get `mvsim` working in Ubuntu if possible
- try `mvsim launch <world-file>`
- stop at the narrowest real Linux-side blocker if it still fails

## In Scope

- verify the current Ubuntu/WSL environment from this repo context
- choose the most practical Linux-side install route for MVSim/MRPT on Ubuntu 24.04
- install required packages or build dependencies inside WSL
- get a real Linux-side `mvsim` command working if possible
- use the repo-local world asset for the first truthful launch attempt
  - accessing the repo through `/mnt/c/...` is acceptable
  - copying the world into Linux temporarily is acceptable if clearly documented
- use the repo-local vehicle asset already prepared
- record exact commands and observed outputs
- if launch succeeds, report the next narrow step before implementing a live pose bridge into the existing Windows-side stack
- if launch fails, stop at the narrowest real blocker and report it precisely
- update docs/operator guidance only as needed to reflect the Linux-side runtime truth

## Desired Outcome

At the end of this round, the repo should be in one of these honest states:

1. `mvsim` is runnable inside Ubuntu/WSL and the first `mvsim launch <world-file>` attempt has completed with real observed results.
2. Ubuntu/WSL is ready, but Linux-side MVSim install/build is blocked by a precise dependency/runtime issue that is now explicitly identified.

What is not acceptable is staying at a generic “WSL is installed” checkpoint without pushing into the actual Linux-side runtime.

## Out Of Scope

- live pose bridge implementation into sim-ingress
- ROS 2 formal adapter
- map-format or occupancy-map design
- autonomous navigation/path planning
- Isaac Sim
- Orin NX packaging
- simulator redesign
- TTS/ASR expansion

## Architecture Constraints

- keep `core` platform-agnostic
- do not redesign the sim stack just because the runtime lives in WSL
- treat this round as Linux-side runtime enablement and bring-up only
- reuse the existing world asset, vehicle asset, live probe, and validation harness where possible
- keep config/path changes explicit and minimal
- keep the bundle narrow and runtime-focused

## Acceptance Criteria

- the round clearly determines whether `mvsim` can run inside the current Ubuntu/WSL environment
- a real Linux-side `mvsim` command is verified, or a precise blocker is reported
- the repo’s minimal world is used in a first Linux-side launch attempt
- exact commands and environment assumptions are documented
- operator/docs surfaces reflect the new truth about Linux-side runtime availability
- focused tests still pass
- existing related tests still pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- whether `mvsim` became runnable inside Ubuntu/WSL
- exact commands used for package install/build and runtime verification
- what Linux-side executable/command now works, if any
- what happened when launching the repo-local world
- whether the round ended in:
  - linux_runtime_enabled
  - linux_runtime_attempted_but_blocked
  - linux_install_blocked
- what the next narrow step is before implementing a live pose bridge
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not expand scope into ROS, simulator redesign, or map-format work.
Stop at the narrowest real blocker and describe it clearly.
