# Current Round Result

## Round
Round 019 - Edge Capability Profile And Config Validation Baseline

## Summary

- Status: PASSED
- The repository now has an explicit deployment capability/profile layer for `dev`, `sim`, and `edge`.
- Obvious config mismatches are now surfaced through one narrow reusable validation seam instead of scattered checks.
- API-visible runtime health/state now expose a concise `deployment_profile` summary.
- Current `edge` config is now clearly reported as a placeholder profile rather than implicitly treated as hardware-ready.

## What I Changed

- Added a focused deployment profile module in:
  - `services/deployment_profile/profile.py`
  - `services/deployment_profile/__init__.py`
- The new profile seam derives:
  - deployment class
  - readiness status
  - expected pose/LLM/audio/recording shape
  - active mock-only components
  - placeholder components
  - validation warnings/errors
- Wired that summary into runtime-facing services:
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
- Added focused tests in:
  - `tests/test_deployment_profile.py`
- Extended API tests in:
  - `tests/test_api_server.py`
- Updated docs:
  - `README.md`
  - `docs/DEPLOYMENT.md`
  - `docs/DEPLOYMENT_PROFILE_CONTRACT.md`

## Exact Files Changed

- `README.md`
- `docs/DEPLOYMENT.md`
- `docs/DEPLOYMENT_PROFILE_CONTRACT.md`
- `services/api_server/runtime.py`
- `services/sim_pose_ingress/runtime.py`
- `services/deployment_profile/__init__.py`
- `services/deployment_profile/profile.py`
- `tests/test_api_server.py`
- `tests/test_deployment_profile.py`
- `coordination/latest_result.md`

## What Capability/Profile Surface I Introduced

New API-visible summary surface:

- `deployment_profile`

Current fields include:

- `profile_name`
- `deployment_class`
- `readiness_status`
- `is_edge_ready`
- `capabilities`
- `configured`
- `supports`
- `mock_components_active`
- `placeholder_components`
- `warnings`
- `errors`

Current deployment classes:

- `dev` -> `dev_only`
- `sim` -> `sim_only`
- `edge` -> `edge_candidate`

Current readiness states:

- `ready_for_profile`
- `placeholder`
- `invalid`

## What Config Validation Rules I Added

### Profile Derivation

Profiles are derived from:

- `env_name`

Supported values:

- `dev`
- `sim`
- `edge`

### Pose Provider Validation

- `dev` expects:
  - `pose_provider_type: mock`
- `sim` expects:
  - `pose_provider_type: sim_ingress`
- `edge` expects:
  - `pose_provider_type: odin_ros`

If that expectation is violated, the profile is marked:

- `readiness_status: invalid`

### Placeholder / Degraded Signals

For `sim`:

- `isaac_source.mode: stub` is surfaced as a warning and placeholder component

For `edge`:

- `narrator_type != local_llm` is surfaced as placeholder
- `llm_backend_type: mock` is surfaced as placeholder
- `audio_output_type: mock` is surfaced as placeholder
- `tts_backend_type: mock` is surfaced as placeholder
- `artifact_player_backend_type: mock` is surfaced as placeholder

If the edge shape is coherent but those placeholders remain active, the profile is marked:

- `readiness_status: placeholder`

## How API-Visible Readiness/Capability Exposure Changed

`MockTourApiRuntime` now exposes `deployment_profile` in:

- `health()`
- `state()`

`SimPoseIngressRuntime` now exposes `deployment_profile` in:

- `health()`
- `state()`

This means API consumers can now see:

- what profile the current config claims to be
- whether it is coherent for that profile
- whether it is still placeholder/mock
- what pose/audio/LLM expectations apply

### Manual Sample

For current `configs/dev.yaml`, the runtime now reports:

```json
{
  "profile_name": "dev",
  "deployment_class": "dev_only",
  "readiness_status": "ready_for_profile",
  "mock_components_active": [
    "mock_pose_provider",
    "mock_tts_backend",
    "mock_artifact_player"
  ],
  "placeholder_components": [],
  "errors": [],
  "warnings": []
}
```

## Which Current Edge Settings Are Still Placeholder/Mock After This Round

Current `configs/edge.yaml` is now explicitly treated as an edge-shape placeholder, not a fully ready hardware config.

The profile layer currently identifies these placeholders:

- `audio_output_type: mock`
- `tts_backend_type: mock`
- `artifact_player_backend_type: mock`

The current edge config still points at:

- `pose_provider_type: odin_ros`
- `narrator_type: local_llm`
- `llm_backend_type: ollama`

So the edge direction is correct, but the audio/output path is still mock-backed.

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_deployment_profile -v`
  - passed
  - `Ran 4 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 67 tests ... OK`

### Manual

Ran an inline runtime sample against `configs/dev.yaml` and captured both:

- `health().deployment_profile`
- `state().deployment_profile`

Confirmed:

- both surfaces report `profile_name: dev`
- both surfaces report `deployment_class: dev_only`
- both surfaces report `readiness_status: ready_for_profile`
- current mock/placeholder components are surfaced explicitly

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 20]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `24fd3cef7366133551a07c5bec9a73c502cb697f`

## Staged / Committed State

- Round 019 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched

## Blockers, Risks, Or Remaining Gaps Before Real Orin NX Or Hardware-Backed Deployment

- The profile layer is a summary/validation seam, not a hardware probe or deployment manager.
- `edge` readiness is still config-declared and validation-based, not device-proven.
- True edge readiness still requires:
  - real `odin_ros` pose integration
  - non-mock audio output / TTS backend
  - hardware-backed playback/device validation
- `sim` still reports stub/live source shape through config intent; it does not yet prove live Isaac availability on its own.
