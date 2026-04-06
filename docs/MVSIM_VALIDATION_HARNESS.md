# MVSim Guided Validation Harness

## Purpose

This document defines the narrow operator-facing validation harness added on top of the current MVSim compatibility path.

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

- sim-ingress reachability
- sim-profile API reachability
- `/debug` availability
- bridge/demo validation status
- route completion
- latest session id
- latest spot / latest narration
- follow-up question result

## How Common Problems Are Reported

Current common operator failures are surfaced as:

- `healthy`
- `unreachable`
- `port_conflict`

Current examples:

- target port occupied but expected health endpoint missing
  - reported as `port_conflict`
- required upstream not reachable
  - reported as `unreachable`
- validation cannot start because local services are still missing
  - reported as `failed_precondition`

## Scope Limits

This harness does not:

- provide live MVSim runtime integration
- redesign simulation architecture
- manage long-running packaged services
- replace `/debug`

It only makes the current PC-side MVSim validation flow much easier for a human to inspect.
