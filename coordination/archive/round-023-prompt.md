# Current Round Prompt

## Round
Round 023 - Deployment Command Manifest And Guided Bring-Up Sheet Baseline

## Goal
Introduce a narrow deployment command-manifest layer for `dev`, `sim`, and `edge` that makes repo-owned bring-up actions explicit, so an operator can see the exact internal-service commands to run, in launch-plan order, without turning the repo into a real launcher or supervisor.

## Why This Is The Current Priority

Rounds 019 through 022 now established:

- deployment profile/capability summaries
- config validation
- preflight/dependency probes
- explicit launch-plan/startup-contract guidance
- aggregated readiness/blocking summary

That means we can now answer:

- what a config claims to be
- what can be probed
- what should start first
- which steps are ready, blocked, optional, or externally unverified

The next unresolved deployment risk is actionability.

Right now an operator can see what is blocked, but still does not have one machine-readable place that says:

- which exact repo-owned commands correspond to each internal startup step
- which config each command should use
- which steps are manual/external and therefore do not map to a repo command
- how to produce a concise bring-up sheet for dev/sim/edge without reading scattered docs

Before touching real Orin NX packaging, automatic startup, or hardware-backed bring-up, we should add one thin command-manifest seam that turns the current launch/readiness stack into a clearer guided bring-up surface.

## In Scope

- introduce a narrow deployment command-manifest layer alongside the existing deployment profile/preflight/launch-plan/readiness service layer
- keep it out of `core`
- define machine-readable command/action entries for repo-owned internal services only, likely including:
  - command id
  - related launch-plan step id
  - command kind
  - script or entrypoint path
  - config argument or profile argument where relevant
  - a concise operator-facing description
- explicitly distinguish launch-plan steps that:
  - map to repo-owned commands
  - remain external/manual and therefore have no repo command
- ensure the command manifest is derived from one clear place rather than hard-coded ad hoc in docs
- add at least one operator-facing inspection entry point, such as:
  - a script that prints a guided bring-up sheet
  - or a machine-readable command manifest printer
- expose a compact command-manifest or bring-up-guide surface in a reusable runtime-visible place if that stays narrow and low-risk
- update docs to explain:
  - how repo-owned startup commands are represented
  - which steps still remain manual/external
  - why this is still not automatic startup
- add focused tests covering:
  - command-manifest derivation for `dev`, `sim`, and `edge`
  - internal-service command mapping
  - external/manual steps having no repo command
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
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep command-manifest logic outside business orchestration
- do not scatter startup command knowledge across unrelated runtime modules or docs
- prefer one narrow reusable command-manifest seam
- build on top of existing profile/preflight/launch-plan/readiness layers rather than replacing them
- do not turn this round into a launcher, daemon manager, or orchestration framework
- do not actually spawn or supervise long-running services from the new code path
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit deployment command-manifest layer
- repo-owned startup commands for dev/sim/edge are derivable from one clear place
- internal-service commands are clearly separated from manual/external steps
- operator-facing output makes bring-up actions more explicit than launch-plan hints alone
- docs clearly explain what the command manifest does and does not automate
- existing tests still pass
- focused new tests for command-manifest behavior pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- exact validation performed
- what deployment command-manifest or bring-up-guide surface you introduced
- how internal startup steps are now mapped to concrete repo-owned commands
- which current steps still remain manual/external with no repo command
- how operators can inspect the command manifest or guided bring-up sheet now
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into real hardware integration, packaging, or automatic startup management.
Stop at the narrowest real blocker and describe it clearly.
