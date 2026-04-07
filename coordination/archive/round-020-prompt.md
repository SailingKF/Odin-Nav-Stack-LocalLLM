# Current Round Prompt

## Round
Round 020 - Edge Preflight And Dependency Probe Baseline

## Goal
Introduce a narrow deployment preflight/probe layer that turns the current `deployment_profile` summary into a more actionable readiness check, especially for `edge`, without attempting real hardware integration.

## Why This Is The Current Priority

Rounds 019 and earlier established:
- explicit deployment profiles for `dev`, `sim`, and `edge`
- config-shape validation
- API-visible readiness summaries

That tells us what a config claims to be.

The next unresolved deployment risk is startup-time ambiguity:
- which dependencies are merely configured
- which dependencies are locally probeable
- which dependencies are missing, unreachable, or still external/unverified

Before touching real Orin NX or hardware-backed integration, we should add a thin preflight layer that can answer:
- what this profile still depends on
- what can be checked now
- what is still only declared by config

## In Scope

- introduce a narrow deployment preflight/probe layer, likely alongside the deployment profile service layer
- keep it out of `core`
- define a concise preflight summary for things such as:
  - route file exists
  - POI file exists
  - session log directory is writable or creatable
  - configured local HTTP dependencies are present or unreachable, when a safe short probe is possible
  - dependencies that remain external/unverified, such as hardware pose or real audio devices
- ensure probes are:
  - best-effort
  - short-timeout
  - safe on a dev machine
  - non-blocking to normal runtime construction
- expose a compact preflight summary in API-visible health/state surfaces alongside `deployment_profile`
- clearly distinguish states like:
  - `ok`
  - `unreachable`
  - `missing`
  - `unverified_external`
  - `not_applicable`
- update docs to explain:
  - what preflight checks currently exist
  - what they do not prove
  - which edge dependencies still remain external after this round
- add focused tests covering:
  - preflight derivation
  - local file checks
  - mocked URL probe outcomes
  - API-visible preflight summary exposure

## Out Of Scope

- actual Orin NX deployment
- ROS/Odin hardware integration
- real audio device playback
- real TTS engine selection
- systemd/service packaging
- containerization work
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep deployment preflight logic outside business orchestration
- do not scatter ad-hoc probes throughout unrelated runtime modules
- prefer one narrow reusable preflight seam
- make probes optional/best-effort rather than startup-blocking
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit deployment preflight/probe layer
- API-visible health or state includes a concise preflight summary
- local file/config checks and safe dependency probes are clearly surfaced
- external/unverified dependencies are explicitly labeled rather than silently assumed ready
- docs clearly explain what current preflight does and does not prove
- existing tests still pass
- focused new tests for preflight behavior pass

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- what preflight/probe surface you introduced
- what checks/probes are now performed
- how API-visible readiness exposure changed
- which current edge dependencies remain external/unverified after this round
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into hardware integration or packaging work.
Stop at the narrowest real blocker and describe it clearly.
