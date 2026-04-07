# Current Round Prompt

## Round
Round 021 - Deployment Launch Plan And Startup Contract Baseline

## Goal
Introduce a narrow launch-plan/startup-contract layer for `dev`, `sim`, and `edge`, so the repo can explicitly describe which processes or external dependencies should be started, in what order, and which readiness gates matter before we attempt real Orin NX or hardware-backed bring-up.

## Why This Is The Current Priority

Rounds 019 and 020 established:
- deployment profile/capability summaries
- config-shape validation
- preflight/dependency probes

That tells us:
- what a config claims to be
- what can be checked at startup time

The next unresolved deployment risk is startup orchestration clarity.

Right now we still do not have one clear, reusable answer for:
- what needs to be started for `dev`
- what needs to be started for `sim`
- what needs to be started for `edge`
- which dependencies are repo-owned processes versus external dependencies
- what order and gating rules an operator should follow

Before touching real Orin NX or hardware integration, we should make that explicit in a thin launch-plan contract.

## In Scope

- introduce a narrow deployment launch-plan/startup-contract layer, likely alongside the profile/preflight service layer
- keep it out of `core`
- define a concise per-profile launch plan describing:
  - repo-owned processes/services to start
  - external dependencies that must exist
  - optional processes
  - startup order
  - readiness gates
- distinguish categories such as:
  - `internal_service`
  - `external_dependency`
  - `optional_service`
- include current repo-relevant examples where appropriate, such as:
  - API server
  - LLM gateway
  - sim pose ingress server
  - hardware pose dependency
  - audio device dependency
- expose a compact launch-plan summary in an API-visible surface or a reusable runtime-accessible helper
- add at least one operator-facing entry point for this information, such as:
  - a small script
  - or a documented API-visible plan surface
- update docs to explain:
  - current dev/sim/edge startup order
  - what the launch plan does and does not automate
  - which edge steps still remain external/manual
- add focused tests covering:
  - launch-plan derivation for each profile
  - startup ordering / categorization
  - API-visible or helper-visible launch-plan exposure

## Out Of Scope

- actual Orin NX deployment
- ROS/Odin hardware integration
- real audio device playback
- real TTS engine selection
- systemd/service packaging
- containerization work
- a full process supervisor
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep launch-plan logic outside business orchestration
- do not scatter startup-order knowledge across unrelated runtime modules
- prefer one narrow reusable startup-contract seam
- do not turn this round into a full launcher/orchestrator framework
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit launch-plan/startup-contract layer
- dev/sim/edge startup expectations are clearly derivable from one place
- repo-owned services and external/manual dependencies are explicitly distinguished
- startup order and readiness gates are documented and machine-readable enough for later reuse
- docs clearly explain current startup guidance without claiming full automation
- existing tests still pass
- focused new tests for launch-plan behavior pass

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- what launch-plan/startup-contract surface you introduced
- how dev/sim/edge startup expectations are now represented
- what current steps remain manual/external for edge
- how operators can inspect the launch plan now
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into real hardware integration or packaging work.
Stop at the narrowest real blocker and describe it clearly.
