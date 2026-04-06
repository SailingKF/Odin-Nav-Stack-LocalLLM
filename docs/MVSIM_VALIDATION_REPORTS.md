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

Latest comparison export artifacts are stored under:

- `session_logs/mvsim_validation_harness/comparison_exports/`

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
- `validation_asset_identity`
- `mvsim_source_kind`
- `proxy_target`
- `service_targets`
- `detail` when useful

## Validation Asset Identity

Each report now includes a compact `validation_asset_identity` block. The goal is not to mirror the whole config. The goal is to capture only the small set of fields needed to decide whether a live run and a compatibility run came from meaningfully comparable validation assets.

Current identity fields are:

- `identity_version`
- `validation_mode`
- `mvsim_mode`
- `config_name`
- `config_path`
- `route_file`
- `poi_file`
- `world_file`
- `vehicle_name`
- `alignment_strategy`
- `motion_strategy`
- `target_spot_id`
- `second_target_spot_id`

Comparison-critical fields are intentionally narrow:

- `route_file`
- `poi_file`
- `world_file`
- `vehicle_name`
- `alignment_strategy`
- `motion_strategy`

Context-only warning fields are:

- `config_name`
- `config_path`

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
- `POST /reports/compare/export`
- `GET /reports/compare/export/latest`

The harness status surface also includes:

- `latest_report`
- `recent_reports`
- `latest_comparison`

This lets an operator inspect the last run without replaying the session.

## Latest Comparison Export Artifact

The harness can now also persist a stable export artifact for the latest already-computed comparison summary.

The export stays intentionally small and file-backed.

Current export fields include:

- `export_id`
- `created_at`
- `export_kind`
- `export_version`
- `harness_url`
- `comparison_status`
- `comparison_available`
- `comparability_status`
- `missing_modes`
- `guardrail_reasons`
- `live_runtime_report`
- `compatibility_shim_report`
- `differences`

This export is generated from the latest persisted comparison inputs only.

It does not:

- rerun validation
- recompute from raw event logs
- broaden into a separate report-generation system

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
- compact validation asset identity

Missing-report cases are explicit:

- `status: "missing_reports"`
- `missing_modes: ["live_runtime"]`
- `missing_modes: ["compatibility_shim"]`
- or both if neither report exists yet

The comparison now also includes explicit guardrails:

- `comparability_status`
  - `comparable`
  - `comparable_with_warnings`
  - `not_directly_comparable`
- `guardrail_reasons`
- `identity_guardrails`

Guardrail behavior is:

- `comparable`
  - required validation assets match
- `comparable_with_warnings`
  - required assets still match, but some identity fields are incomplete or only config-context fields differ
- `not_directly_comparable`
  - one or more required validation assets differ, or one side is missing the identity block entirely

This keeps the harness from silently implying that two latest reports are fair to compare when they were produced with different validation assets.

## Scope Limits

These reports are intentionally narrow:

- no database
- no generic telemetry warehouse
- no long-term analytics pipeline
- no attempt to persist every internal event

They are concise operator-facing summaries of what actually happened in each harness validation run.
