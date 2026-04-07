# Current Round Prompt

## Round
Round 029 - MVSim Minimal Integration And End-To-End Tour Validation Baseline

## Goal
Introduce a narrow MVSim-oriented simulator integration or compatibility path that can drive the existing simulation-ingress interface and complete one full end-to-end guided-tour validation on PC, without bringing in Isaac or redesigning the simulation stack.

## Why This Is The Current Priority

The PC-side stack is now mature enough that continuing to polish deployment/operator metadata has lower value than closing the next real unknown: can a lightweight external simulator drive the existing tour system end-to-end without relying on Isaac?

For this project, the current priority is not high-fidelity quadruped dynamics. The real product risks are:

- pose-driven POI triggering
- narration flow
- operator control and observation
- session visibility
- a simulator-side path that can later evolve toward richer map/sim integration

That means a planar mobile-robot simulation path is sufficient for this stage, and MVSim is the intended lightweight direction for this round.

## In Scope

- introduce an MVSim-oriented simulator-side publisher, adapter, or runner path that produces planar pose updates for the current stack
- reuse the existing external simulation-ingress HTTP contract rather than inventing a new runtime path:
  - `/runtime/start`
  - `/poses`
  - `/poses/batch`
  - `/stream/finish`
- keep the work on the simulator-side or adapter-side seam
- validate one complete simulated tour run on PC using the existing stack:
  - simulator-side pose source or playback path
  - `sim_pose_ingress`
  - `api_server`
  - current tour state/session flow
  - current `/debug`-backed API surfaces
- add the minimum focused docs needed to explain:
  - what was integrated
  - how to run the demo
  - what is real MVSim usage versus compatibility scaffolding
- add focused tests for the new adapter/publisher logic where practical
- add one or more focused scripts that make this end-to-end validation runnable by an engineer on PC

## Acceptable Shape For This Round

This round does not have to become a polished full simulator product.

An acceptable result is:

- a thin MVSim-oriented publisher bridge
- a constrained compatibility runner clearly designed around MVSim-style planar mobile-robot simulation
- a runnable end-to-end validation path that uses the real external pose-ingress interface

What is not acceptable is silently falling back to just another generic stub with no meaningful MVSim-oriented integration value.

If any compatibility shim is used, document it explicitly in the result.

## Out Of Scope

- Isaac Sim
- ROS formal adapter
- Orin NX deployment
- supervisor or service-manager work
- real hardware pose sources
- real TTS engine selection
- ASR
- map editor work
- map-format design
- rich 3D perception or sensor simulation
- complex locomotion or quadruped dynamics
- broad simulator abstraction rewrites

## Architecture Constraints

- keep `core` platform-agnostic
- do not rewrite the existing simulation stack
- reuse the current sim-ingress and publisher-side seams where possible
- favor planar `x/y` pose flow; a wheeled-robot assumption is acceptable for this stage
- keep the bundle coherent and narrow
- do not mix this round with ROS migration or map-format design
- do not introduce a heavy dependency explosion just to chase simulator purity
- preserve current API, narrator, session, and audio behavior

## Acceptance Criteria

- repository contains a clear MVSim-oriented integration or compatibility path
- a developer on PC can run one end-to-end simulated tour validation through the existing stack
- the validation goes through the real external pose-ingress/API path, not only an internal mock shortcut
- the result clearly states what used real MVSim behavior and what remains scaffolding
- focused tests pass
- existing related tests still pass
- the result gives exact run commands for the PC validation flow

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- whether this used real MVSim runtime, a compatibility shim, or a mixed approach
- exact commands used to run the PC validation
- what end-to-end behavior was verified
- what APIs and services were exercised
- exact validation performed
- what MVSim-oriented integration surface now exists
- what still remains before map-format work or ROS-side integration should start
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not expand scope into Isaac, ROS formalization, map-format work, or packaging.
Stop at the narrowest real blocker and describe it clearly.
