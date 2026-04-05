# Deployment Verification Manifest Contract

## Purpose

This document defines the narrow verification-manifest layer that sits on top of:

- deployment command manifest
- deployment readiness

The goal is to make post-start success checks explicit for repo-owned services without turning the repository into a launcher, poller, or process supervisor.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/verification_manifest.py`

Operator-facing inspection entry point:

- `scripts/print_verification_sheet.py`

Current runtime-facing exposure:

- `deployment_verification_manifest`

Related one-shot execution layer:

- `services/deployment_profile/verification_runner.py`
- `deployment_endpoint_contract`

## Current Top-Level Surface

The verification manifest exposes:

- `profile_name`
- `config_path`
- `verifications`
- `steps`
- `verification_count`
- `repo_verification_step_count`
- `manual_step_count`

This means:

- repo-owned post-start verification checks are available from one reusable place
- manual/external steps remain explicit and intentionally have no repo verification contract
- the repo still does not auto-poll or wait on long-running services
- repo-owned verification URLs now derive from the endpoint contract instead of hard-coded defaults

## Verification Entry Shape

Each repo-owned verification currently exposes:

- `verification_id`
- `step_id`
- `command_id`
- `order`
- `profile_name`
- `verification_kind`
- `method`
- `base_url`
- `target_path`
- `target_url`
- `expected_statuses`
- `expected_fields`
- `description`

Current verification kind:

- `http_json_health`

## Step Verification Mapping Shape

Each launch-plan step is also summarized in the manifest with:

- `step_id`
- `order`
- `name`
- `action_type`
- `verification_type`
- `verification_available`
- `verification_id`
- `verification_target`
- `detail`

Current verification types:

- `repo_verification`
- `manual_external`
- `manual_optional`

## Current Repo-Owned Verification Mapping

### dev

Repo-owned verifications currently map:

- `llm_gateway`
  - `GET http://127.0.0.1:9000/health`
  - expected fields:
    - `service`
    - `active_backend_type`
    - `fallback_active`
- `api_server`
  - `GET http://127.0.0.1:8000/health`
  - expected fields:
    - `service`
    - `env_name`
    - `deployment_profile`

Manual/non-verifiable steps remain:

- `ollama_runtime`
- `debug_browser`

### sim

Repo-owned verifications currently map:

- `sim_pose_ingress_server`
  - `GET http://127.0.0.1:8100/health`
  - expected fields:
    - `service`
    - `ingress_contract`
    - `deployment_profile`
- `api_server`
  - `GET http://127.0.0.1:8000/health`

Manual/non-verifiable steps remain:

- `isaac_live_dependency`
- `isaac_stub_source`
- `sim_publisher_bridge`

### edge

Repo-owned verifications currently map:

- `llm_gateway`
  - `GET http://127.0.0.1:9000/health`
- `api_server`
  - `GET http://127.0.0.1:8000/health`

Manual/non-verifiable steps remain:

- `hardware_pose_dependency`
- `ollama_runtime`
- `audio_device_dependency`

## Guided Bring-Up Verification Sheet

The current operator-facing verification sheet is derived from:

- `deployment_readiness`
- `deployment_command_manifest`
- `deployment_verification_manifest`

It provides:

- current readiness status
- repo command to run when available
- verification URL to inspect after startup
- expected success statuses and fields
- blocking reasons when present

Use:

```text
python scripts/print_verification_sheet.py --config configs/dev.yaml
python scripts/print_verification_sheet.py --config configs/sim.yaml
python scripts/print_verification_sheet.py --config configs/edge.yaml
```

## What This Layer Does Not Automate

This layer does not yet:

- start services automatically
- wait for services to become ready
- continuously poll health endpoints
- retry failed services
- package services for Orin NX

It only centralizes:

- repo-owned post-start success checks
- verification-to-step mapping
- operator-facing bring-up verification guidance

For the one-shot execution and result-summary layer built on top of this manifest, see:

- `docs/DEPLOYMENT_VERIFICATION_RUNNER_CONTRACT.md`
- `docs/DEPLOYMENT_ENDPOINT_CONTRACT.md`
