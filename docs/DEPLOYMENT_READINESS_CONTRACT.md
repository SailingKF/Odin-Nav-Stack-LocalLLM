# Deployment Readiness Contract

## Purpose

This document defines the narrow deployment-readiness aggregation layer that combines:

- deployment profile
- deployment preflight
- deployment launch plan

into one operator-facing readiness view.

The goal is to make blockers and partially verifiable external steps easier to read without turning the repo into a launcher or supervisor.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/readiness.py`

Operator-facing inspection entry point:

- `scripts/print_readiness_report.py`

Current runtime-facing exposure:

- `deployment_readiness`

## Current Top-Level Surface

The readiness surface exposes:

- `profile_name`
- `profile_readiness_status`
- `overall_status`
- `required_ready_count`
- `required_blocked_count`
- `required_external_unverified_count`
- `optional_step_count`
- `not_applicable_step_count`
- `step_count`
- `blocking_reasons`
- `steps`

## Per-Step Statuses

Current per-step readiness statuses are:

- `ready`
- `blocked`
- `optional`
- `external_unverified`
- `not_applicable`

### Meaning

- `ready`
  - the step is required and its current gates are satisfied
- `blocked`
  - the step is required and is blocked by a missing/unreachable dependency or failed gate
- `optional`
  - the step is optional and does not currently need stronger action
- `external_unverified`
  - the step is required but depends on something external that this repo can only label, not prove
- `not_applicable`
  - the step exists in the plan shape but does not currently apply for this config

## Overall Status Meanings

Current overall statuses are:

- `blocked`
- `external_verification_needed`
- `ready_for_guided_bringup`
- `ready_with_placeholders`

### Meaning

- `blocked`
  - at least one required step is blocked, or the profile itself is invalid
- `external_verification_needed`
  - no required steps are blocked, but at least one required step remains externally unverified
- `ready_for_guided_bringup`
  - required steps are currently readable as ready within the current repo boundaries
- `ready_with_placeholders`
  - guided bring-up is coherent, but placeholder/mock profile conditions still remain

## How Readiness Is Derived

This layer does not invent separate deployment logic.

It derives readiness from:

- `deployment_profile`
  - profile-level validity / placeholder state
- `deployment_preflight`
  - current local checks and safe probes
- `deployment_launch_plan`
  - startup steps, categories, ordering, and readiness gates

## What It Does Not Guarantee

This layer does not guarantee:

- that services are already started
- that real hardware is publishing correctly
- that real audio playback works end-to-end
- that startup automation exists
- that processes are supervised or restartable

It is a reporting and aggregation seam only.
