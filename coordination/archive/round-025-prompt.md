# Current Round Prompt

## Round
Round 025 - Deployment Verification Runner And Result Summary Baseline

## Goal
Introduce a narrow one-shot deployment verification-runner layer for `dev`, `sim`, and `edge` that can execute the repo-owned verification manifest checks once and produce a concrete pass/fail result summary, without turning the repo into a poller, waiter, or process supervisor.

## Why This Is The Current Priority

Rounds 019 through 024 now established:

- deployment profile/capability summaries
- config validation
- preflight/dependency probes
- explicit launch-plan/startup-contract guidance
- aggregated readiness/blocking summary
- explicit repo-owned command mapping
- explicit repo-owned verification mapping

That means we can now answer:

- what a config claims to be
- what should start first
- what is currently blocked
- what command to run
- what success endpoint or health surface should be checked afterward

The next unresolved deployment risk is execution of those checks.

Right now an operator can see which verification URL or health contract should be used, but still does not have one machine-readable place that says:

- what happened when those repo-owned checks were actually run once
- which verification checks passed
- which ones failed due to unreachable service, bad status, or missing fields
- how to get a concise result summary after startup without manually interpreting raw HTTP responses

Before touching real Orin NX packaging, automatic startup, or active waiting logic, we should add one thin verification-runner seam that executes existing repo verification contracts once and reports the result.

## In Scope

- introduce a narrow deployment verification-runner layer alongside the existing deployment profile/preflight/launch-plan/readiness/command-manifest/verification-manifest service layer
- keep it out of `core`
- support one-shot execution of repo-owned verification checks only
- start with the currently defined verification kind:
  - `http_json_health`
- validate things such as:
  - target reachable vs unreachable
  - response JSON `status` in expected statuses
  - expected fields present
- define machine-readable verification result entries, likely including:
  - verification id
  - step id
  - result status
  - observed status value
  - missing fields if any
  - error detail if unreachable or invalid
- include a concise overall result summary, such as:
  - passed verification count
  - failed verification count
  - skipped/manual step count
  - overall result status
- add at least one operator-facing inspection entry point, such as:
  - a script that runs the one-shot checks and prints a result summary
- optionally expose a reusable helper surface for runtime or scripts if that stays narrow and does not imply long-lived state
- update docs to explain:
  - what the verification runner does
  - what it checks
  - what it does not do
  - why it is still not an active waiter or poller
- add focused tests covering:
  - successful verification result
  - unreachable target result
  - missing expected field result
  - result summary rendering or aggregation

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
- active polling loops
- wait-until-ready logic
- retries/backoff
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep verification-runner logic outside business orchestration
- do not scatter one-shot verification execution logic across unrelated runtime modules or docs
- prefer one narrow reusable verification-runner seam
- build on top of existing verification-manifest contracts rather than duplicating them
- do not turn this round into a launcher, waiter, daemon manager, or orchestration framework
- do not actually start services from the new code path
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit one-shot deployment verification-runner layer
- repo-owned verification checks can be executed from one clear place
- results clearly distinguish passed, failed, and non-repo/manual steps
- operator-facing output makes verification outcomes more explicit than raw target URLs alone
- docs clearly explain what the runner does and does not automate
- existing tests still pass
- focused new tests for verification-runner behavior pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- exact validation performed
- what verification-runner or result-summary surface you introduced
- how repo-owned verification checks are now executed once and summarized
- what result statuses are now used
- how operators can run the one-shot verification summary now
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into real hardware integration, packaging, active waiting, or automatic startup management.
Stop at the narrowest real blocker and describe it clearly.
