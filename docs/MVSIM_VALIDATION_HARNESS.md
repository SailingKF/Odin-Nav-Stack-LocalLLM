# MVSim Guided Validation Harness

## Purpose

This document defines the narrow operator-facing validation harness added on top of the current MVSim path.

The goal is to let a human validate the current PC-side simulation path from one local page instead of manually coordinating:

- multiple terminals
- bridge runs
- repeated REST calls

This is not a general supervisor or deployment manager.
It is a local validation seam for PC acceptance only.

## What The Harness Is

Current implementation lives in:

- `services/mvsim_validation_harness/runtime.py`
- `services/mvsim_validation_harness/app.py`
- `services/mvsim_validation_harness/static/index.html`

Runnable entry point:

- `scripts/run_mvsim_validation_harness.py`

## How A Human Should Use It

### Easiest path

Run:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim.yaml --open-browser
```

Then use the local page:

- `Start / Attach Local Stack`
- `Run MVSim Validation`
- `Open /debug`

### Manual page URL

If you do not use `--open-browser`, open:

- `http://127.0.0.1:8300/harness`

## Current Interaction Model

The harness supports both:

- attach to already-running local services
- launch local services itself when ports are free

Current launched services are intentionally narrow:

- sim pose ingress server
- sim-profile API server

The harness does **not** try to become a general multi-service supervisor.

## What Checks Are Visible

The harness currently surfaces at least:

- configured MVSim mode
- effective MVSim mode
- live-runtime availability
- WSL installability status
- whether the current shell is elevated
- sim-ingress reachability
- sim-profile API reachability
- `/debug` availability
- bridge/demo validation status
- route completion
- latest session id
- latest spot / latest narration
- follow-up question result
- the configured live alignment strategy
- the expected first live POI for the current repo-local MVSim validation asset

With the Round 033 WSL runtime update, the harness can now also truthfully show:

- that a live MVSim runtime is available in WSL even while the validated end-to-end flow still uses `compatibility_shim`
- which runtime host is configured for live MVSim bring-up
- whether the repo-local world asset is already compatible with the current Linux-side MVSim parser
- which live pose topic and bridge mode are currently configured for the next bridge step

## How Common Problems Are Reported

Current common operator failures are surfaced as:

- `healthy`
- `unreachable`
- `port_conflict`
- `blocked_live_runtime`

Current examples:

- target port occupied but expected health endpoint missing
  - reported as `port_conflict`
- required upstream not reachable
  - reported as `unreachable`
- validation cannot start because local services are still missing
  - reported as `failed_precondition`
- validation is switched to `live_runtime` but no real `mvsim` runtime is available
  - reported as `blocked_live_runtime_unavailable`
- WSL path is the recommended next step but the current shell is not elevated
  - surfaced through the WSL enablement section and probe blocker details

## Scope Limits

This harness does not:

- redesign simulation architecture
- manage long-running packaged services
- replace `/debug`

It makes the current PC-side MVSim validation flow much easier for a human to inspect.
It also distinguishes three truths cleanly:

- compatibility shim works now
- live runtime may already be available in WSL
- a minimal live pose bridge may now be available even if full live route progression is still pending
