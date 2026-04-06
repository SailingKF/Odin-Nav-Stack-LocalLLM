# MVSim Validation Reports

## Purpose

This document defines the narrow report artifact written by the MVSim validation harness after each validation run.

The goal is simple:

- leave behind durable operator evidence
- keep the artifact human-readable
- avoid turning the harness into a database or analytics system

## Storage Location

Reports are stored under:

- `session_logs/mvsim_validation_harness/reports/`

Each completed harness validation writes one JSON file.

Current file naming shape:

- `<utc_timestamp>-<validation_mode>.json`

Example:

- `20260406T120100Z-live_runtime.json`
- `20260406T120200Z-compatibility_shim.json`

## What The Report Includes

Each report currently includes at least:

- `report_id`
- `created_at`
- `status`
- `validation_mode`
- `mvsim_mode`
- `config_path`
- `config_name`
- `harness_url`
- `debug_url`
- `passed`
- `session_id`
- `latest_spot_name`
- `latest_narration_text`
- `route_completed`
- `live_first_poi_hit_occurred`
- `live_second_poi_hit_occurred`
- `live_second_narration_occurred`
- `recent_triggered_spot_ids`
- `recent_narrated_spot_ids`
- `mvsim_source_kind`
- `proxy_target`
- `service_targets`
- `detail` when useful

## Truthfulness Rules

The report must keep compatibility and live truth claims explicit:

- `validation_mode: "compatibility_shim"` means replay-based validation
- `validation_mode: "live_runtime"` means the truthful WSL MVSim bridge path ran

Live-specific truth fields are only meaningful when the run used `live_runtime`:

- `live_first_poi_hit_occurred`
- `live_second_poi_hit_occurred`
- `live_second_narration_occurred`

For compatibility runs, those fields may remain `false`.

## API Surfaces

The harness now exposes report data through:

- `GET /reports/latest`
- `GET /reports/recent`
- `GET /reports/compare`

The harness status surface also includes:

- `latest_report`
- `recent_reports`
- `latest_comparison`

This lets an operator inspect the last run without replaying the session.

## Latest Live Vs Compatibility Comparison

The harness now also exposes a compact comparison between:

- the latest available `live_runtime` report
- the latest available `compatibility_shim` report

The comparison stays intentionally small.

Current compared fields include:

- pass/fail
- route completion
- first live POI hit truth
- second live POI hit truth
- recent triggered spots
- recent narrated spots
- latest spot name
- config name when useful through the compact report views

Missing-report cases are explicit:

- `status: "missing_reports"`
- `missing_modes: ["live_runtime"]`
- `missing_modes: ["compatibility_shim"]`
- or both if neither report exists yet

## Scope Limits

These reports are intentionally narrow:

- no database
- no generic telemetry warehouse
- no long-term analytics pipeline
- no attempt to persist every internal event

They are concise operator-facing summaries of what actually happened in each harness validation run.
