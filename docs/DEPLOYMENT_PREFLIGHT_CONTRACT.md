# Deployment Preflight Contract

## Purpose

This document defines the narrow deployment preflight/probe layer that sits alongside the deployment profile summary.

The goal is to answer:

- what this config still depends on
- what can be safely checked now
- what remains external or unverified

without turning startup into real hardware integration.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/preflight.py`

It is currently exposed by:

- `services/api_server/runtime.py`
- `services/sim_pose_ingress/runtime.py`

## Current Summary Surface

The preflight surface is:

- `deployment_preflight`

Current top-level fields:

- `profile_name`
- `summary_status`
- `http_timeout_sec`
- `counts`
- `checks`

## Check Status Meanings

Current per-check statuses are:

- `ok`
- `unreachable`
- `missing`
- `unverified_external`
- `not_applicable`

## Current Checks

### Local File/Directory Checks

- `route_file`
- `poi_file`
- `session_log_dir`

These verify:

- configured content files exist
- session log directory can be created and written

### Local HTTP Dependency Probes

When applicable, current short-timeout URL probes include:

- `llm_gateway`
  - probes `.../health`
- `ollama_runtime`
  - probes `.../api/tags`

These are:

- best-effort
- short-timeout
- safe to run on a dev machine
- non-blocking to runtime construction

### External / Unverified Dependency Markers

Current external labels include:

- `hardware_pose_dependency`
  - for `pose_provider_type: odin_ros`
- `isaac_live_dependency`
  - for `sim_ingress` with `isaac_source.mode: live`
- `audio_device_dependency`
  - when current audio mode implies a non-mock playback path

These are intentionally marked:

- `unverified_external`

because this round does not attempt real hardware, real audio device, or real simulator runtime integration.

## What Preflight Does Not Prove

Current preflight does not prove:

- ROS/Odin topics are really present
- real audio playback works end-to-end
- simulator live adapters are actually attached
- an LLM runtime is correct beyond basic reachability
- a given environment is fully field-ready

It only provides:

- a concise startup-time readiness snapshot
- file/config sanity checks
- safe local HTTP reachability checks
- explicit labeling of still-external dependencies
