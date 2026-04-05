# Deployment Launch Plan Contract

## Purpose

This document defines the narrow launch-plan/startup-contract layer that sits alongside:

- deployment profile
- deployment preflight

The goal is to make startup order and ownership explicit without turning the repo into a full process supervisor.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/launch_plan.py`

Operator-facing inspection entry point:

- `scripts/print_launch_plan.py`

Current runtime-facing exposure:

- `deployment_launch_plan`

## Current Top-Level Surface

The launch-plan summary exposes:

- `profile_name`
- `automation_level`
- `steps`
- `step_count`
- `required_step_count`
- `categories`

Current automation level:

- `manual_guided`

This means:

- the repo can describe startup order and gating
- the repo does not yet auto-start or supervise all services

## Step Shape

Each step currently exposes:

- `step_id`
- `order`
- `category`
- `required`
- `name`
- `startup_hint`
- `readiness_gates`
- `detail`

## Current Categories

- `internal_service`
- `external_dependency`
- `optional_service`

## Current Profile Startup Expectations

### dev

Current intent:

- start local Ollama first when configured
- then start the repo-owned LLM gateway
- then start the API server
- optionally open the `/debug` page

### sim

Current intent:

- decide whether the simulator source is:
  - stub
  - live external
- start the sim pose ingress server
- optionally start the publisher bridge
- optionally start the API/debug server

### edge

Current intent:

- ensure hardware pose dependency exists externally
- ensure local LLM runtime exists externally when required
- start the repo-owned LLM gateway
- start the repo-owned API server
- treat audio-device bring-up as optional until edge moves beyond mock audio

## What The Launch Plan Does Not Automate

This layer does not yet:

- supervise processes
- restart crashed services
- manage systemd
- package containers
- prove real hardware pose, audio, or simulator readiness

It only provides:

- machine-readable startup order
- step ownership/categorization
- readiness gates
- a lightweight operator guidance surface
