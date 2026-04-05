# Deployment Verification Runner Contract

## Purpose

This document defines the narrow one-shot verification-runner layer that sits on top of:

- deployment verification manifest
- deployment command manifest
- deployment readiness

The goal is to execute repo-owned verification checks once and produce a concrete pass/fail summary without turning the repository into a poller, waiter, or process supervisor.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/verification_runner.py`

Operator-facing inspection entry point:

- `scripts/run_verification_summary.py`

## Current Top-Level Run Result Surface

The one-shot runner currently returns:

- `profile_name`
- `config_path`
- `overall_result_status`
- `verification_result_count`
- `passed_verification_count`
- `failed_verification_count`
- `skipped_manual_step_count`
- `results`
- `steps`

## Current Result Statuses

Repo-owned verification result statuses:

- `passed`
- `failed_unreachable`
- `failed_invalid_status`
- `failed_missing_fields`
- `failed_invalid_payload`
- `failed_unsupported_kind`

Manual/non-repo step result statuses:

- `manual_external`
- `manual_optional`

Current overall runner statuses:

- `passed`
- `failed`
- `manual_only`

## What The Runner Checks

Current supported verification kind:

- `http_json_health`

For each repo-owned verification, the runner executes the check once and validates:

- target reachable vs unreachable
- JSON payload shape
- `status` field value against expected statuses
- expected fields present in the response body

The runner does not currently:

- retry
- poll repeatedly
- wait until ready
- start services automatically

## Current Verification Result Entry Shape

Each repo-owned verification result currently exposes:

- `verification_id`
- `step_id`
- `command_id`
- `verification_kind`
- `target_url`
- `result_status`
- `observed_status`
- `missing_fields`
- `error_detail`

Each step-level summary entry currently exposes:

- `step_id`
- `name`
- `result_status`
- `verification_available`
- `verification_target`
- `observed_status`
- `missing_fields`
- `error_detail`

## Guided Verification Result Summary

The current result summary layer combines:

- bring-up verification sheet
- one-shot runner result

It preserves operator-facing fields such as:

- startup status
- repo command
- verification target
- expected statuses
- blocking reasons

while adding:

- one-shot result status
- observed service status
- missing fields
- verification failure detail

## How To Run It

Use:

```text
python scripts/run_verification_summary.py --config configs/dev.yaml
python scripts/run_verification_summary.py --config configs/sim.yaml
python scripts/run_verification_summary.py --config configs/edge.yaml
```

Optional timeout override:

```text
python scripts/run_verification_summary.py --config configs/edge.yaml --timeout-sec 1.5
```

## What This Layer Does Not Automate

This layer does not yet:

- start services
- wait for services to become healthy
- continuously poll health targets
- retry failed targets
- manage packaging or startup automation for Orin NX

It only provides:

- a single execution of repo-owned verification checks
- a machine-readable result summary
- a clear distinction between passed checks, failed checks, and manual/non-repo steps
