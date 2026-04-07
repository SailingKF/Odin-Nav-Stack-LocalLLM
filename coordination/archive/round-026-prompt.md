# Current Round Prompt

## Round
Round 026 - Deployment Endpoint Contract And Config-Driven Target Baseline

## Goal
Introduce a narrow deployment endpoint-contract layer for repo-owned services so startup commands, verification manifests, and result summaries derive their target URLs and ports from one clear source instead of relying on hard-coded defaults.

## Why This Is The Current Priority

Rounds 019 through 025 now established:

- deployment profile/capability summaries
- config validation
- preflight/dependency probes
- launch-plan/startup-contract guidance
- readiness/blocking summary
- command manifest
- verification manifest
- one-shot verification runner

That means we can now answer:

- what should start
- what is blocked
- what command to run
- what verification target to check
- what happened when the check ran once

The next unresolved deployment risk is source-of-truth drift.

Right now repo-owned verification targets are still effectively tied to built-in default URLs and ports. That is acceptable for the current laptop defaults, but it will become fragile when we begin tightening edge/Orin deployment assumptions or changing bind settings.

We need one thin endpoint-contract seam that answers:

- what the repo-owned local endpoint is for each internal service
- which values come from config vs defaults
- how command/verification/reporting layers stay aligned when ports or hosts change

Before touching packaging, real edge deployment, or active bring-up automation, we should eliminate this target drift risk.

## In Scope

- introduce a narrow deployment endpoint-contract layer alongside the current deployment profile/preflight/launch-plan/readiness/command-manifest/verification-manifest/verification-runner service layer
- keep it out of `core`
- define machine-readable endpoint entries for repo-owned internal services, likely including:
  - service id / step id
  - bind host
  - port
  - base URL
  - source of value:
    - config-driven
    - defaulted
- support current repo-owned services where relevant, such as:
  - `llm_gateway`
  - `api_server`
  - `sim_pose_ingress_server`
- make verification manifest derive target URLs from the endpoint contract instead of hard-coded URLs
- make command-manifest or operator-facing surfaces reuse the same endpoint contract where useful
- add at least one operator-facing inspection entry point, such as:
  - a script that prints the endpoint contract for a config
  - or a compact endpoint section in an existing deployment surface
- update docs to explain:
  - how endpoint values are derived
  - which values currently come from config
  - which values currently remain defaults
  - why this is still not service discovery or a launcher
- add focused tests covering:
  - endpoint derivation for `dev`, `sim`, and `edge`
  - config override behavior where applicable
  - verification target alignment with the derived endpoint contract

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
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep endpoint-contract logic outside business orchestration
- do not scatter repo-owned endpoint knowledge across unrelated runtime modules, scripts, and docs
- prefer one narrow reusable endpoint-contract seam
- build on top of existing deployment surfaces rather than replacing them
- do not turn this round into dynamic service discovery, launch orchestration, or networking abstraction sprawl
- preserve current dev, sim, API, narrator, and audio behavior
- keep this as one coherent bundle only

## Acceptance Criteria

- repository contains an explicit deployment endpoint-contract layer
- repo-owned endpoint URLs/ports are derivable from one clear place
- verification targets reuse the derived endpoint contract
- operator-facing output makes endpoint assumptions more explicit than current hard-coded target behavior
- docs clearly explain what the endpoint contract does and does not automate
- existing tests still pass
- focused new tests for endpoint-contract behavior pass

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- exact validation performed
- what endpoint-contract surface you introduced
- how repo-owned service targets are now derived from config/defaults
- which targets remain defaulted vs explicitly configured
- how operators can inspect the endpoint contract now
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps before real Orin NX or hardware-backed deployment

If you hit a blocker, do not expand scope into packaging, service discovery, or automatic startup management.
Stop at the narrowest real blocker and describe it clearly.
