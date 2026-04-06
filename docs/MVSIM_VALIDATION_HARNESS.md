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
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --open-browser
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
- select an explicit validation mode:
  - `compatibility_shim`
  - `live_runtime`

Current launched services are intentionally narrow:

- sim pose ingress server
- sim-profile API server

Current isolated harness config:

- `configs/sim_harness.yaml`
- local sim ingress target:
  - `http://127.0.0.1:8110`
- local API target:
  - `http://127.0.0.1:8001`

This keeps operator validation off the machine-global default `8000` path.

The harness does **not** try to become a general multi-service supervisor.

## What Checks Are Visible

The harness currently surfaces at least:

- selected validation mode
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
- the expected second live POI for the current repo-local MVSim validation asset
- whether the current live validation truthfully saw:
  - first-stop hit
  - second-stop hit
  - route completion

With the live-harness baseline, the harness can now also truthfully show:

- that a live MVSim runtime is available in WSL
- which runtime host is configured for live MVSim bring-up
- whether the repo-local world asset is already compatible with the current Linux-side MVSim parser
- which live pose topic and bridge mode are currently configured for the current bridge step
- whether the current validation run used:
  - compatibility replay
  - truthful live MVSim pose relay

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
- validation is switched to `live_runtime` but the bridge execution itself fails
  - reported as `failed_bridge_execution`
- WSL path is the recommended next step but the current shell is not elevated
  - surfaced through the WSL enablement section and probe blocker details

## Scope Limits

This harness does not:

- redesign simulation architecture
- manage long-running packaged services
- replace `/debug`

It makes the current PC-side MVSim validation flow much easier for a human to inspect.
It also distinguishes these truths cleanly:

- compatibility shim works now
- live runtime is available in WSL
- the harness can run the truthful live MVSim path itself
- the harness can do that on an isolated local stack without depending on the machine-global `8000` port

## Validation Report Artifacts

Each completed harness validation run now writes one durable JSON report under:

- `session_logs/mvsim_validation_harness/reports/`

The report keeps the run concise and operator-readable.

Current essentials include:

- timestamp
- validation mode
- config path
- pass/fail
- session id
- route completion
- first/second live stop truth
- recent triggered spots
- recent narrated spots
- debug URL and service targets

Current read surfaces:

- `GET /reports/latest`
- `GET /reports/recent`
- `GET /reports/compare`
- harness status also includes:
  - `latest_report`
  - `recent_reports`
  - `latest_comparison`

This means an operator can inspect the most recent validation result later without replaying the run.
It also means the harness can now show a compact latest live-vs-compatibility sanity check without rerunning either path.
