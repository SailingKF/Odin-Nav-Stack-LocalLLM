# Current Round Prompt

## Round
Round 022 - Deployment Readiness Report And Blocking Summary Baseline (Retry)

## Goal
Introduce a narrow deployment-readiness aggregation layer that combines:

- deployment profile
- deployment preflight
- deployment launch plan

into one operator-meaningful readiness view for `dev`, `sim`, and `edge`, so we can answer not just "what should start" but also "what is ready, blocked, optional, or still externally unverified" before later Orin NX or hardware-backed bring-up.

## Why This Is The Current Priority

Rounds 019 through 021 established:

- deployment profile/capability summaries
- config validation
- preflight/dependency probes
- explicit launch-plan/startup-contract guidance

That means we now know:

- what a config claims to be
- what can be probed
- what order components should be started in

The next unresolved deployment risk is that an operator still has to mentally join those three layers together.

Right now we still do not have one clear, reusable answer for:

- which required startup steps are currently ready
- which ones are blocked by missing or unreachable dependencies
- which steps are optional
- which dependencies remain external and therefore only partially verifiable
- whether a given profile is reasonably ready for guided bring-up

Before touching real Orin NX packaging, startup automation, or hardware-backed bring-up, we should create one thin readiness-report seam that makes this visible without turning the repo into a real supervisor.

Current retry note:

- a draft readiness module exists, but the bundle is not complete yet
- the current repo state does not yet show:
  - export/wiring through `services/deployment_profile/__init__.py`
  - runtime/API exposure in existing runtime surfaces
  - focused readiness tests
  - docs or operator-facing inspection entry point
  - updated `coordination/latest_result.md`

This retry should finish the whole coherent bundle rather than only adding one helper module.

## In Scope

- introduce a narrow deployment-readiness aggregation layer alongside the current deployment profile/preflight/launch-plan service layer
- keep it out of `core`
- derive a concise readiness view from existing deployment surfaces rather than duplicating their logic
- define an explicit per-step readiness summary for launch-plan steps, with states such as:
  - `ready`
  - `blocked`
  - `optional`
  - `external_unverified`
  - `not_applicable`
- include an overall summary that is useful to an operator, such as:
  - overall readiness status
  - count of required ready steps
  - count of blocked required steps
  - count of external-unverified required steps
  - key blocking reasons
- expose this readiness view in at least one reusable runtime-visible surface, likely alongside:
  - `deployment_profile`
  - `deployment_preflight`
  - `deployment_launch_plan`
- add at least one operator-facing inspection entry point, such as:
  - a small script
  - or a compact API-visible summary
- update docs to explain:
  - how readiness is derived from current deployment surfaces
  - what `blocked` versus `external_unverified` means
  - why this is still not full startup automation
- add focused tests covering:
  - readiness derivation for `dev`, `sim`, and `edge`
  - blocked versus optional versus external-unverified behavior
  - runtime/API-visible readiness exposure
- ensure the repo-visible result is complete enough that a reviewer can verify it from:
  - `coordination/latest_result.md`
  - git status
  - concrete code references

## Out Of Scope

- actual Orin NX deployment
- ROS/Odin hardware integration
- real audio device playback
- real TTS engine selection
- systemd/service packaging
- containerization work
- auto-starting processes
- crash supervision
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep readiness/reporting logic outside business orchestration
- do not scatter step-readiness logic across unrelated runtime modules
- prefer one narrow reusable aggregation seam
- build on top of existing profile/preflight/launch-plan layers rather than replacing them
- do not turn this round into a launcher, daemon manager, or orchestration framework
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only
- do not stop after adding only an internal helper module

## Acceptance Criteria

- repository contains an explicit deployment-readiness aggregation layer
- readiness is derived from existing deployment surfaces in one clear place
- required startup steps can be understood as ready, blocked, optional, or externally unverified
- operator-facing output makes blockers more obvious than raw preflight or launch-plan data alone
- docs clearly explain what the readiness report does and does not guarantee
- existing tests still pass
- focused new tests for readiness aggregation pass
- `coordination/latest_result.md` is updated to reflect the real completed bundle

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- exact validation performed
- what deployment-readiness surface you introduced
- how readiness is derived from profile/preflight/launch-plan
- what statuses are now used for per-step readiness
- what current `edge` blockers or external-unverified steps look like in the new surface
- how operators can inspect the readiness report now
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into real hardware integration, packaging, or automatic startup management.
Stop at the narrowest real blocker and describe it clearly.
