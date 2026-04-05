# Deployment Profile Contract

## Purpose

This document defines the narrow deployment capability/profile layer used to summarize what a given config is expected to support.

The goal is to keep environment-specific readiness logic out of `core/` while still making `dev`, `sim`, and `edge` intent explicit.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/profile.py`
- `services/deployment_profile/preflight.py`

It is consumed by runtime-facing services such as:

- `services/api_server/runtime.py`
- `services/sim_pose_ingress/runtime.py`

## Current Profile Names

Supported profiles are derived from `env_name`:

- `dev`
- `sim`
- `edge`

## Current Summary Surface

Each derived profile exposes:

- `profile_name`
- `deployment_class`
- `readiness_status`
- `is_edge_ready`
- `capabilities`
- `configured`
- `supports`
- `mock_components_active`
- `placeholder_components`
- `warnings`
- `errors`

## Current Deployment Classes

- `dev` -> `dev_only`
- `sim` -> `sim_only`
- `edge` -> `edge_candidate`

## Readiness Meanings

- `ready_for_profile`
  - current config is coherent for the selected profile
- `placeholder`
  - profile shape is coherent, but some target-critical subsystems are still mock or placeholder
- `invalid`
  - at least one obvious config mismatch exists

## Current Validation Rules

### dev

Expected pose provider:

- `mock`

### sim

Expected pose provider:

- `sim_ingress`

Current placeholder surfaced when:

- `isaac_source.mode: stub`

### edge

Expected pose provider:

- `odin_ros`

Current edge-placeholder signals include:

- mock audio output
- mock TTS backend
- mock artifact player
- mock LLM backend
- non-`local_llm` narrator

## Why This Stays Outside Core

This layer is not business logic.

It exists to:

- summarize deployment intent
- flag obvious environment mismatches
- expose concise readiness information to operators and API clients

It should not:

- change POI behavior
- change orchestrator transitions
- hardcode environment checks deep inside `core/`

## Current Limitations

- the profile layer is a focused summary/validation seam, not a full deployment manager
- it does not install dependencies or prove real hardware readiness
- `edge` can still be `placeholder` even when the API is healthy
- true Orin NX readiness still depends on real pose, audio, and service integration later

For current startup-time dependency checks, see:

- `docs/DEPLOYMENT_PREFLIGHT_CONTRACT.md`
