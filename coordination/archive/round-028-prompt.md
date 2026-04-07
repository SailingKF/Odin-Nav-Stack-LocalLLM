# Current Round Prompt

## Round
Round 028 - Deployment Config Hygiene And Deprecation Summary Baseline

## Goal
Introduce a narrow deployment config-hygiene summary layer that makes legacy compatibility usage, mixed endpoint config state, and migration guidance explicit for operators, without removing backward compatibility yet.

## Why This Is The Current Priority

Rounds 019 through 027 now established:

- deployment profile/capability summaries
- config validation
- preflight/dependency probes
- launch-plan/startup-contract guidance
- readiness/blocking summary
- command manifest
- verification manifest
- verification runner
- endpoint contract
- endpoint config canonicalization

That means the repo can now derive targets correctly, but operators still lack one concise answer to:

- which configs are already canonicalized
- which configs still rely on legacy compatibility
- which services are partially canonicalized vs fully canonicalized
- what migration action is recommended next

Right now this information exists implicitly in source labels and docs, but not yet as a dedicated operator-facing hygiene summary.

Before edge/Orin deployment guidance becomes stricter, we should add one thin config-hygiene layer that surfaces deprecation and migration status without breaking current configs.

## In Scope

- introduce a narrow deployment config-hygiene summary layer alongside the current endpoint config canonicalization and endpoint contract layers
- keep it out of `core`
- define operator-facing hygiene/deprecation signals, likely including:
  - overall config hygiene status
  - whether legacy compatibility fields are still in use
  - whether canonical endpoint config is present for each repo-owned service
  - whether a config is fully canonicalized, mixed, or mostly defaulted
  - recommended migration actions
- start with endpoint-related config hygiene only; do not broaden into general config linting
- make the hygiene layer machine-readable and reusable by scripts/runtime surfaces
- add at least one operator-facing inspection entry point, such as:
  - a script that prints the config hygiene summary
  - or a compact runtime-visible summary surface
- update docs to explain:
  - what config hygiene statuses mean
  - how to move from legacy compatibility usage to canonical config
  - what is recommended but not yet mandatory
- add focused tests covering:
  - fully canonicalized config
  - legacy-only config
  - mixed canonical plus legacy config
  - recommended-action generation

## Out Of Scope

- actual Orin NX deployment
- ROS/Odin hardware integration
- real audio device playback
- real TTS engine selection
- systemd/service packaging
- containerization work
- service discovery
- reverse proxying
- auto-starting processes
- active polling/waiting
- large config-schema refactors unrelated to service endpoints
- actual removal of backward compatibility in this round
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep config-hygiene logic outside business orchestration
- do not scatter migration/deprecation knowledge across unrelated runtime modules, scripts, and docs
- prefer one narrow reusable hygiene-summary seam
- build on top of the existing endpoint canonicalization and endpoint contract layers
- preserve backward compatibility for current configs
- do not turn this round into a general config-framework overhaul or a breaking cleanup
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit endpoint-focused config-hygiene summary layer
- operators can clearly tell whether a config is canonicalized, mixed, legacy-dependent, or default-heavy
- recommended migration actions are visible without reading code
- docs clearly explain hygiene/deprecation meanings and migration intent
- existing tests still pass
- focused new tests for config-hygiene behavior pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- exact validation performed
- what config-hygiene or deprecation-summary surface you introduced
- what hygiene statuses now exist
- how legacy compatibility usage is reported
- what recommended migration actions are surfaced
- how operators can inspect the hygiene summary now
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into packaging, service discovery, or automatic startup management.
Stop at the narrowest real blocker and describe it clearly.
