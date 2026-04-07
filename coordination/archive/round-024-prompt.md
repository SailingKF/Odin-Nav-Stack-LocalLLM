# Current Round Prompt

## Round
Round 024 - Deployment Verification Manifest And Success Check Baseline

## Goal
Introduce a narrow deployment verification-manifest layer for `dev`, `sim`, and `edge` that makes post-start success checks explicit for repo-owned services, so an operator can see not just what command to run, but how to verify that the service is actually up.

## Why This Is The Current Priority

Rounds 019 through 023 now established:

- deployment profile/capability summaries
- config validation
- preflight/dependency probes
- explicit launch-plan/startup-contract guidance
- aggregated readiness/blocking summary
- explicit repo-owned command mapping

That means we can now answer:

- what a config claims to be
- what can be probed before startup
- what should start first
- which steps are currently blocked
- which repo-owned command corresponds to each internal service

The next unresolved deployment risk is post-start verification clarity.

Right now an operator can see:

- what command to run
- what is currently blocked before startup

but still does not have one machine-readable place that says:

- how to verify a repo-owned service after it is started
- which endpoint, state field, or health check should be inspected
- what success looks like for API server vs LLM gateway vs sim ingress service
- which steps remain manual/external and therefore do not have a repo verification contract

Before touching real Orin NX packaging, automatic startup, or hardware-backed bring-up, we should add one thin verification-manifest seam that completes the operator bring-up story without creating a launcher.

## In Scope

- introduce a narrow deployment verification-manifest layer alongside the existing deployment profile/preflight/launch-plan/readiness/command-manifest service layer
- keep it out of `core`
- define machine-readable verification entries for repo-owned internal services only, likely including:
  - verification id
  - related launch-plan step id
  - related command id when applicable
  - verification kind
  - endpoint path, URL shape, or runtime surface to inspect
  - expected success condition or status shape
  - a concise operator-facing description
- explicitly distinguish launch-plan steps that:
  - have repo verification checks
  - remain manual/external and therefore have no repo verification contract
- ensure verification mapping is derived from one clear place rather than hard-coded ad hoc in docs
- add at least one operator-facing inspection entry point, such as:
  - a script that prints a bring-up plus verification sheet
  - or a machine-readable verification manifest printer
- expose a compact verification-manifest or verification-guide surface in a reusable runtime-visible place if that stays narrow and low-risk
- update docs to explain:
  - how repo-owned startup verification is represented
  - which steps still remain manual/external with no repo verification contract
  - why this is still not automatic startup or process supervision
- add focused tests covering:
  - verification-manifest derivation for `dev`, `sim`, and `edge`
  - internal-service verification mapping
  - external/manual steps having no repo verification contract
  - runtime/API-visible or script-visible exposure

## Out Of Scope

- actual Orin NX deployment
- ROS/Odin hardware integration
- real audio device playback
- real TTS engine selection
- systemd/service packaging
- containerization work
- auto-starting processes
- crash supervision
- running long-lived services as part of tests
- active polling loops or process waiting logic
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep verification-manifest logic outside business orchestration
- do not scatter post-start success-check knowledge across unrelated runtime modules or docs
- prefer one narrow reusable verification-manifest seam
- build on top of existing profile/preflight/launch-plan/readiness/command-manifest layers rather than replacing them
- do not turn this round into a launcher, waiter, daemon manager, or orchestration framework
- do not actually start, stop, poll, or supervise long-running services from the new code path
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit deployment verification-manifest layer
- repo-owned post-start verification checks for dev/sim/edge are derivable from one clear place
- internal-service verification checks are clearly separated from manual/external steps
- operator-facing output makes post-start success criteria more explicit than startup hints alone
- docs clearly explain what the verification manifest does and does not automate
- existing tests still pass
- focused new tests for verification-manifest behavior pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- exact validation performed
- what deployment verification-manifest or verification-guide surface you introduced
- how repo-owned services are now mapped to concrete post-start verification checks
- which current steps still remain manual/external with no repo verification contract
- how operators can inspect the verification manifest or bring-up verification sheet now
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into real hardware integration, packaging, or automatic startup management.
Stop at the narrowest real blocker and describe it clearly.
