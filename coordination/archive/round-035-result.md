# Current Round Result

## Round
Round 035 - Live Route Alignment And First Narration Trigger Baseline

## Summary

- Status: `live_first_narration_enabled`
- This round closed the next product-level event boundary after live pose relay.
- The narrow alignment strategy chosen was:
  - keep the current route and POI content unchanged
  - keep the existing WSL MVSim live-pose bridge unchanged
  - align only the repo-local minimal MVSim world init pose to the first current POI
- The first truthful live runtime pose now lands at:
  - `x = 0.0`
  - `y = 0.0`
  - `label = "tour_bot"`
- A real live POI hit occurred for:
  - `gate`
  - `East Gate`
- A real live-triggered narration event occurred for:
  - `East Gate`
- `/debug` remained available and the existing Windows-side API state now exposes the real narration text produced by that live hit.

## What I Changed

- Aligned the repo-local MVSim world init pose to the first current POI:
  - `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`
- Recorded the alignment strategy explicitly in sim config:
  - `configs/sim.yaml`
- Extended the live runtime probe so operators can see the live alignment choice:
  - `services/sim_publisher_bridge/mvsim_live.py`
- Extended the live bridge demo so it prints a concise validation result summary:
  - `scripts/run_mvsim_live_bridge_demo.py`
- Updated the harness page to surface:
  - `Live Alignment Strategy`
  - `Expected First Live POI`
  - `services/mvsim_validation_harness/static/index.html`
- Added focused tests for:
  - live alignment probe surface
  - first-live-narration summary logic
  - `tests/test_mvsim_live_runtime.py`
  - `tests/test_mvsim_live_bridge.py`
- Updated focused docs:
  - `docs/MVSIM_LIVE_POSE_BRIDGE.md`
  - `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`
  - `README.md`

## Exact Files Changed

- `README.md`
- `configs/sim.yaml`
- `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`
- `docs/MVSIM_LIVE_POSE_BRIDGE.md`
- `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `scripts/run_mvsim_live_bridge_demo.py`
- `services/mvsim_validation_harness/static/index.html`
- `services/sim_publisher_bridge/mvsim_live.py`
- `tests/test_mvsim_live_bridge.py`
- `tests/test_mvsim_live_runtime.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Alignment Strategy Chosen

Chosen strategy:

- `world_init_pose_matches_first_route_poi`

What that means:

- the current POI content remains the source of truth
- no simulator redesign was introduced
- no core/orchestrator logic was changed
- the repo-local MVSim validation world now starts the robot at the first current POI:
  - `East Gate` at `(0.0, 0.0)`

Why this was chosen:

- it is the narrowest truthful change that can validate one real live POI hit and one real live narration event
- it keeps the live bridge, sim-ingress, and API proxy surfaces intact
- it makes the alignment choice explicit in `configs/sim.yaml`

## Whether A Live POI Hit Occurred

Yes.

Truthful live POI hit facts observed:

- live pose reached the Windows-side stack as:
  - `{"x": 0.0, "y": 0.0, "label": "tour_bot"}`
- live bridge demo summary reported:
  - `live_poi_hit_occurred: true`
  - `validated_spot_id: "gate"`
  - `validated_spot_name: "East Gate"`
  - `matches_expected_first_spot: true`

## Whether A Live Narration Event Occurred

Yes.

Truthful narration facts observed:

- live bridge demo summary reported:
  - `live_narration_occurred: true`
- sim-profile API state reported:
  - `last_narration_text = "Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI."`
- latest session reported:
  - `latest_narration_text` with the same `East Gate` narration
  - `latest_audio_playback.spot_name = "East Gate"`

## Exact Commands Used

### Live probe

```text
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
```

### Focused tests

```text
python -m unittest tests.test_mvsim_live_runtime -v
python -m unittest tests.test_mvsim_live_bridge -v
python -m unittest tests.test_mvsim_validation_harness -v
python -m unittest tests.test_api_server -v
python -m unittest discover -s tests
```

### Real live validation flow

Start sim ingress:

```text
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Start sim-profile API proxy:

```text
python scripts/run_api_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8000
```

Run the real live bridge:

```text
python scripts/run_mvsim_live_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100 --sample-count 3
```

Observe API and debug page:

```text
GET http://127.0.0.1:8000/state
GET http://127.0.0.1:8000/session/latest
GET http://127.0.0.1:8000/debug
```

## What End-To-End Live Fact Was Actually Validated

The truthful live fact validated in this round is:

- a real WSL MVSim pose sample from `/tour_bot/pose` reached the current Windows-side `sim_pose_ingress`
- that live sample fell inside the first current POI trigger radius
- the existing Windows-side tour runtime emitted a real `East Gate` narration event
- the sim-profile API proxy reflected that narration through `/state`, `/session/latest`, and `/debug`

Exact observed downstream facts:

- API state:
  - `api_mode = "sim_ingress_proxy"`
  - `state = "NAVIGATING"`
  - `active_spot_name = "Central Plaza"`
  - `last_pose = {"x": 0.0, "y": 0.0, "label": "tour_bot"}`
  - `last_narration_text = "Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI."`
- Latest session:
  - `latest_event_type = "session_finished"`
  - `latest_narration_text` equals the `East Gate` narration
  - `latest_audio_playback.spot_id = "gate"`
  - `latest_audio_playback.spot_name = "East Gate"`
- Debug page:
  - `GET /debug` returned `200`

What this does **not** validate yet:

- natural continuous live motion across multiple POIs
- a second live POI hit
- full live route completion

## Whether The Round Ended In `live_first_narration_enabled`, `live_poi_hit_without_narration`, Or `live_alignment_blocked`

This round ended in:

- `live_first_narration_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. decide whether the repo-local MVSim validation world should stay a first-hit-only asset or gain a minimal truthful controlled motion path
2. if that can be done without broadening scope, validate a second live POI hit
3. keep the route/POI contract explicit and avoid broad simulator redesign

## Exact Validation Performed

### Probe validation

- `python scripts/print_mvsim_live_probe.py --config configs/sim.yaml`
- verified:
  - `runtime_available: true`
  - `live_pose_surface.topic_name: "/tour_bot/pose"`
  - `live_validation_alignment.strategy: "world_init_pose_matches_first_route_poi"`
  - `live_validation_alignment.target_spot_name: "East Gate"`

### Focused unit validation

- `python -m unittest tests.test_mvsim_live_runtime -v`
  - passed
- `python -m unittest tests.test_mvsim_live_bridge -v`
  - passed
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed
- `python -m unittest tests.test_api_server -v`
  - passed

### Full regression validation

- `python -m unittest discover -s tests`
  - passed
  - `Ran 116 tests ... OK`

### Real live smoke validation

- launched:
  - sim pose ingress server on `127.0.0.1:8100`
  - sim-profile API server on `127.0.0.1:8000`
- ran:
  - `python scripts/run_mvsim_live_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100 --sample-count 3`
- observed from `live_validation_summary`:
  - `live_pose_reached_stack: true`
  - `live_poi_hit_occurred: true`
  - `live_narration_occurred: true`
  - `validated_spot_id: "gate"`
  - `validated_spot_name: "East Gate"`
  - `alignment_strategy: "world_init_pose_matches_first_route_poi"`
  - `matches_expected_first_spot: true`
- observed from API:
  - `last_narration_text` populated with the real `East Gate` narration
  - `active_spot_name` advanced to `Central Plaza`
- observed from UI surface:
  - `/debug` returned `200`

## Current Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 37]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_live_bridge_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `2a1f6e6f09096480506f107958fd47d08ddf015e`

## Whether Files Are Staged And/Or Committed

- repo code/doc bundle for Round 035:
  - committed
- currently staged:
  - no
- `coordination/latest_result.md`:
  - updated locally after commit only
  - not staged
  - not committed

## Blockers, Risks, Or Remaining Gaps

- the current live validation world is now explicitly a first-hit baseline, not a natural route-completion world
- no truthful second live POI hit has been validated yet
- `docs/DEV_WORKFLOW.md` still has a separate pre-existing local modification outside this round
- temp smoke directories remain untracked and were intentionally not included in the commit
