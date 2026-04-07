# Current Round Prompt

## Round
Round 027 - Deployment Endpoint Config Canonicalization Baseline

## Goal
Introduce a narrow deployment endpoint-config canonicalization layer so repo-owned service targets derive from one explicit config shape, while preserving backward compatibility with existing fields such as `llm_gateway_url`.

## Why This Is The Current Priority

Rounds 019 through 026 now established:

- deployment profile/capability summaries
- config validation
- preflight/dependency probes
- launch-plan/startup-contract guidance
- readiness/blocking summary
- command manifest
- verification manifest
- verification runner
- endpoint contract

That means we can now answer:

- what should start
- what is blocked
- what command to run
- what target to verify
- what happened when the check ran
- what endpoint each repo-owned service assumes

The next unresolved deployment risk is config-shape inconsistency.

Right now endpoint derivation works, but it still mixes:

- historical config fields such as `llm_gateway_url`
- newer `service_endpoints.<service_id>.*` overrides
- default values

This is still workable, but it means the repo does not yet have one fully canonical config story for internal service targets.

Before tightening edge/Orin deployment guidance any further, we should make the config source-of-truth clearer while remaining backward compatible.

## In Scope

- introduce a narrow endpoint-config canonicalization layer alongside the current deployment endpoint-contract layer
- keep it out of `core`
- define one preferred explicit config shape for repo-owned service targets, likely under:
  - `service_endpoints.<service_id>`
- preserve backward compatibility for current historical fields where needed, especially:
  - `llm_gateway_url`
- make endpoint derivation report not just whether a value is config-driven, but whether it came from:
  - canonical endpoint config
  - legacy compatibility field
  - default
- update the endpoint contract implementation to prefer the canonical shape when both are present
- keep command-manifest, verification-manifest, and verification-runner aligned with the canonicalized endpoint derivation
- update example configs where appropriate to demonstrate the preferred shape, but do not break existing flows
- add focused docs explaining:
  - the preferred endpoint config shape
  - backward compatibility behavior
  - precedence rules when both new and legacy fields exist
- add focused tests covering:
  - canonical config path
  - legacy compatibility path
  - precedence when both are present
  - verification target alignment after canonicalization

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
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep endpoint-config logic outside business orchestration
- do not scatter endpoint precedence knowledge across unrelated runtime modules, scripts, and docs
- prefer one narrow reusable endpoint canonicalization seam
- build on top of the existing endpoint contract rather than replacing it wholesale
- preserve backward compatibility for current configs
- do not turn this round into a general config-framework overhaul
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit canonical endpoint-config story for repo-owned services
- endpoint derivation has clear precedence between canonical config, legacy fields, and defaults
- verification targets and command args remain aligned with the derived endpoint contract
- docs clearly explain the preferred config shape and backward compatibility behavior
- existing tests still pass
- focused new tests for canonicalization behavior pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- exact validation performed
- what canonical endpoint-config behavior you introduced
- what the preferred service endpoint config shape is now
- how legacy fields such as `llm_gateway_url` are handled
- what precedence rules now apply
- how operators can inspect or understand the canonicalized endpoint contract now
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into packaging, service discovery, or automatic startup management.
Stop at the narrowest real blocker and describe it clearly.
