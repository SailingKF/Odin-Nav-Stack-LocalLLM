# Current Round Result

## Round
Round 042 - Human-Readable Comparison Export Baseline

## Summary

- Status: `human_readable_comparison_export_enabled`
- This round added a compact human-readable companion export for the latest comparison export path.
- The chosen strategy was:
  - keep JSON export as the source of truth
  - generate a Markdown companion artifact from the already-built latest comparison export payload
  - store the Markdown file alongside the JSON export with the same export id
- The harness can now emit both machine-readable JSON and human-readable Markdown exports without rerunning validation.

## What I Changed

- Added a compact Markdown renderer for the latest comparison export:
  - `services/mvsim_validation_harness/reporting.py`
- Extended the comparison export store so one export operation can persist:
  - JSON export
  - Markdown companion export
  - `services/mvsim_validation_harness/reporting.py`
- Exposed latest human-readable export metadata through the harness runtime:
  - `services/mvsim_validation_harness/runtime.py`
- Added a narrow human-readable export API surface:
  - `GET /reports/compare/export/latest/human`
  - `services/mvsim_validation_harness/app.py`
- Added a small harness UI affordance:
  - `Open Human Export`
  - `services/mvsim_validation_harness/static/index.html`
- Added focused tests for:
  - Markdown rendering
  - Markdown companion persistence
  - human-readable export endpoint
  - `tests/test_mvsim_validation_reporting.py`
  - `tests/test_mvsim_validation_harness.py`
- Updated docs:
  - `docs/MVSIM_VALIDATION_REPORTS.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`
  - `README.md`

## Exact Files Changed

- `README.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `docs/MVSIM_VALIDATION_REPORTS.md`
- `services/mvsim_validation_harness/app.py`
- `services/mvsim_validation_harness/reporting.py`
- `services/mvsim_validation_harness/runtime.py`
- `services/mvsim_validation_harness/static/index.html`
- `tests/test_mvsim_validation_harness.py`
- `tests/test_mvsim_validation_reporting.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## What Human-Readable Export Strategy Was Chosen

Chosen strategy:

- reuse the latest comparison export payload from Round 041
- render one compact Markdown companion file from that payload
- keep the Markdown export small and scan-friendly
- keep it file-backed and colocated with the JSON export
- avoid any new document/report generation system

## Where The Human-Readable Artifacts Are Stored

Human-readable comparison companion exports are stored under:

- `session_logs/mvsim_validation_harness/comparison_exports/`

Current naming shape:

- JSON:
  - `<export_id>.json`
- Markdown:
  - `<export_id>.md`

Real example from this round:

- JSON:
  - `session_logs/mvsim_validation_harness/comparison_exports/20260406T140401Z-latest_comparison_export.json`
- Markdown:
  - `session_logs/mvsim_validation_harness/comparison_exports/20260406T140401Z-latest_comparison_export.md`

## What The Human-Readable Export Includes

The Markdown companion includes only high-signal operator fields:

- export id
- created-at timestamp
- comparison status
- comparability status
- missing modes
- guardrail reasons
- compact live report summary
- compact compatibility report summary
- compared outcome flags

The identity sections are rendered as compact one-line summaries such as:

- `world=... | vehicle=... | route=... | poi=... | align=... | motion=...`

## Whether The Harness Can Now Emit Both JSON And Human-Readable Latest Comparison Exports

Yes.

The current export flow is:

1. build the latest comparison summary
2. build the JSON export payload
3. render a Markdown companion from that export payload
4. persist both under the same export id

No validation rerun is required.

## How Missing-Comparison Cases Are Represented

Missing-comparison cases remain explicit in both export forms:

- JSON:
  - `comparison_status: "missing_reports"`
  - `comparison_available: false`
  - `missing_modes`
  - missing-side report payloads remain `null`
- Markdown:
  - `Comparison Status: missing_reports`
  - `Missing Modes: <...>`
  - missing-side report summary fields render as `N/A`

## Exact Commands Used

### Focused tests

```text
python -m unittest tests.test_mvsim_validation_reporting -v
python -m unittest tests.test_mvsim_validation_harness -v
```

### Full regression

```text
python -m unittest discover -s tests
```

### Real harness operator validation

Start the harness:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8306
```

Check the page:

```text
GET http://127.0.0.1:8306/harness
```

Export the current latest comparison:

```text
POST http://127.0.0.1:8306/reports/compare/export
```

Read the latest human-readable export:

```text
GET http://127.0.0.1:8306/reports/compare/export/latest/human
```

Inspect human-export metadata from status:

```text
GET http://127.0.0.1:8306/status
```

## What Operator Fact Was Actually Validated

The truthful operator facts validated in this round are:

1. one export action now produces:
   - JSON export
   - Markdown companion export
2. the Markdown artifact is stored under the same stable repo-local export directory
3. the harness can return the latest human-readable export directly over HTTP
4. the Markdown content is scan-friendly and preserves the current truth state of the latest comparison

Real observed export from this round:

- `export_id = "20260406T140401Z-latest_comparison_export"`
- `json_path = "C:\\Users\\saili\\Desktop\\odin_nav_stack_local_llm_docs\\session_logs\\mvsim_validation_harness\\comparison_exports\\20260406T140401Z-latest_comparison_export.json"`
- `markdown_path = "C:\\Users\\saili\\Desktop\\odin_nav_stack_local_llm_docs\\session_logs\\mvsim_validation_harness\\comparison_exports\\20260406T140401Z-latest_comparison_export.md"`
- `comparison_status = "ready"`
- `comparability_status = "not_directly_comparable"`

Observed Markdown snippet:

- `# Latest Comparison Export`
- `- Comparison Status: ready`
- `- Comparability Status: not_directly_comparable`

## Whether The Round Ended In `human_readable_comparison_export_enabled`, `human_readable_comparison_export_partially_enabled`, Or `human_readable_comparison_export_blocked`

This round ended in:

- `human_readable_comparison_export_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. optionally add a tiny download button label or separate operator text hint on the harness page
2. keep the Markdown export compact and resist broadening into long-form reports
3. if needed later, add a minimal index/listing of recent human-readable exports without introducing analytics/history UI

## Exact Validation Performed

### Focused unit validation

- `python -m unittest tests.test_mvsim_validation_reporting -v`
  - passed
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed

### Full regression validation

- `python -m unittest discover -s tests`
  - passed
  - `Ran 128 tests ... OK`

### Real harness operator smoke

- launched:
  - `python scripts/run_mvsim_validation_harness.py --config configs/sim_harness.yaml --host 127.0.0.1 --port 8306`
- observed:
  - `GET /harness`
  - returned `200`
- exported the current latest comparison:
  - `POST /reports/compare/export`
- observed returned paths:
  - JSON export path
  - Markdown export path
- read the latest human-readable export:
  - `GET /reports/compare/export/latest/human`
  - returned `200`
- observed first lines of real Markdown content:
  - `# Latest Comparison Export`
  - `- Export ID: 20260406T140401Z-latest_comparison_export`
  - `- Comparison Status: ready`
  - `- Comparability Status: not_directly_comparable`
- inspected `/status.latest_comparison_human_export` and confirmed:
  - `export_id`
  - `human_readable_export_path`
  - `content`
  were all present

## Current Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 44]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_live_bridge_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `6f334829d9687fd27f00cf5215f538521f9aea1f`

## Whether Files Are Staged And/Or Committed

- repo code/doc bundle for Round 042:
  - committed
- currently staged:
  - no
- `coordination/latest_result.md`:
  - updated locally
  - not staged
  - not committed

## Blockers, Risks, Or Remaining Gaps

- the Markdown export is intentionally concise and does not try to become a narrative report
- the current latest comparison may still be a truthful non-comparable pair, and the Markdown export preserves that exact truth state
- the human-readable endpoint returns rendered Markdown text directly instead of a separate UI page, which is intentional for narrow operator sharing
- `docs/DEV_WORKFLOW.md` still has a separate pre-existing local modification outside this round
- temp smoke directories remain untracked and were intentionally not included in the commit
