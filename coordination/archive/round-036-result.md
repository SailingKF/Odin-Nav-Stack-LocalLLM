# Current Round Result

## Round
Round 036 - Live Second POI Progression And Minimal Multi-Stop Motion Baseline

## Summary

- Status: `live_second_poi_enabled`
- This round extended the truthful live MVSim path beyond the first stop without broadening into simulator redesign.
- The chosen narrow strategy was:
  - keep the existing Windows-side stack unchanged
  - keep the existing WSL live pose bridge unchanged
  - use an explicit isolated live-validation world and vehicle
  - use a deterministic forward lane for the validation asset only
- A truthful second live POI hit occurred for:
  - `plaza`
  - `Central Plaza`
- A truthful second live-triggered narration event occurred for:
  - `Central Plaza`
- A small extra alignment step also truthfully yielded:
  - `gallery`
  - `History Gallery`
  - full current-route completion in the existing stack

## What I Changed

- Added an explicit live-validation vehicle with fixed forward motion:
  - `content/sim/mvsim/definitions/odin_tour_bot_live_progress.vehicle.xml`
- Added an explicit isolated live-validation world:
  - `content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml`
- Updated sim config to record the live multistop alignment strategy, motion strategy, and expected second stop:
  - `configs/sim.yaml`
- Extended session summaries so live validation can truthfully inspect recent triggered POIs and recent narrations:
  - `core/session/logger.py`
- Extended live bridge summaries so operators can see:
  - first-stop hit truth
  - second-stop hit truth
  - second narration truth
  - route completion truth
  - observed triggered/narrated spot lists
  - `services/sim_publisher_bridge/mvsim_live.py`
- Updated the validation harness UI to surface the expected second live POI:
  - `services/mvsim_validation_harness/static/index.html`
- Updated focused tests for the new live-summary semantics:
  - `tests/test_mvsim_live_bridge.py`
  - `tests/test_mvsim_live_runtime.py`
- Updated operator-facing docs:
  - `README.md`
  - `docs/MVSIM_LIVE_POSE_BRIDGE.md`
  - `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`

## Exact Files Changed

- `README.md`
- `configs/sim.yaml`
- `content/sim/mvsim/definitions/odin_tour_bot_live_progress.vehicle.xml`
- `content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml`
- `core/session/logger.py`
- `docs/MVSIM_LIVE_POSE_BRIDGE.md`
- `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `services/mvsim_validation_harness/static/index.html`
- `services/sim_publisher_bridge/mvsim_live.py`
- `tests/test_mvsim_live_bridge.py`
- `tests/test_mvsim_live_runtime.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Motion / Progression Strategy Chosen

Chosen strategy:

- `isolated_live_validation_world_with_forward_motion`

Recorded motion strategy:

- `constant_forward_velocity_along_demo_axis`

What that means:

- the current route and POI content stay unchanged
- the bridge path from WSL MVSim into Windows `sim_pose_ingress` stays unchanged
- the multi-stop proof uses an explicit validation-only world and vehicle pair
- the validation lane is intentionally deterministic rather than autonomous

Truthful blocker sequence discovered during this round:

1. the first forward-motion attempt stopped near `x~=2.11`
2. the immediate blocker was the internal wall segment:
   - `<pt>2.4 -0.3</pt> <pt>5.2 -0.3</pt>`
3. after removing that wall, the straight `y=0` path still only touched `Central Plaza` tangentially
4. the narrow final fix was to shift the validation lane to:
   - `init_pose: 0.0 0.5 0.0`

This remains an explicit validation asset choice, not a claim of general simulator autonomy.

## Whether A Truthful Second Live POI Hit Occurred

Yes.

Truthful observed facts:

- `recent_poi_triggers` recorded:
  - `gate`
  - `plaza`
  - `gallery`
- live summary reported:
  - `live_second_poi_hit_occurred: true`
  - `expected_second_spot_id: "plaza"`
  - `expected_second_spot_name: "Central Plaza"`
  - `matches_expected_second_spot: true`

## Whether A Truthful Second Live Narration Event Occurred

Yes.

Truthful observed facts:

- `recent_narrations` recorded:
  - `East Gate`
  - `Central Plaza`
  - `History Gallery`
- live summary reported:
  - `live_second_narration_occurred: true`
- the existing stack produced the `Central Plaza` narration through the real live path before continuing on to the final stop

## Whether Full Live Route Completion Occurred

Yes.

This was not the minimum acceptance target, but it did occur truthfully in the same narrow validation asset.

Truthful observed facts:

- `api_state.route_completed = true`
- `api_state.current_index = 3`
- `latest_triggered_spot_id = "gallery"`
- `latest_narrated_spot_id = "gallery"`
- `latest_narration_text` became the generated `History Gallery` narration

## Exact Commands Used

### Live probe

```text
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
```

### Focused tests

```text
python -m unittest tests.test_mvsim_live_runtime -v
python -m unittest tests.test_mvsim_live_bridge -v
python -m unittest tests.test_sim_pose_ingress -v
python -m unittest tests.test_api_server -v
python -m unittest tests.test_mvsim_validation_harness -v
python -m unittest discover -s tests
```

### Real live validation flow

Start sim ingress:

```text
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Start sim-profile API proxy:

```text
python scripts/run_api_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8001
```

Run the real live bridge:

```text
python scripts/run_mvsim_live_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100 --sample-count 180
```

Observe API and debug page:

```text
GET http://127.0.0.1:8001/state
GET http://127.0.0.1:8001/session/latest
GET http://127.0.0.1:8001/debug
```

Note:

- port `8000` was already occupied by another local process, so this round used `8001` for the API proxy during live validation

## What End-To-End Live Fact Was Actually Validated

The truthful live fact validated in this round is:

- a real WSL MVSim pose stream from `/tour_bot/pose` reached the current Windows-side `sim_pose_ingress`
- that live stream truthfully hit:
  - `East Gate`
  - `Central Plaza`
  - `History Gallery`
- the existing Windows-side tour runtime truthfully produced live-triggered narration events for all three current stops
- the current route truthfully completed in the existing stack

Exact observed downstream facts from the successful smoke:

- API state:
  - `route_completed = true`
  - `current_index = 3`
  - `active_spot_name = null`
  - `last_pose = {"x": 9.075166702270508, "y": 0.5, "label": "tour_bot"}`
  - `last_narration_text = "The History Gallery is the final stop in the demo tour. It shows that the guide flow can finish a multi-POI route without duplicate triggers."`
- Latest session:
  - `latest_triggered_spot_id = "gallery"`
  - `latest_narrated_spot_id = "gallery"`
  - `recent_poi_triggers = ["gate", "plaza", "gallery"]`
  - `recent_narrations = ["gate", "plaza", "gallery"]`
- Live bridge summary:
  - `live_pose_reached_stack: true`
  - `live_first_poi_hit_occurred: true`
  - `live_second_poi_hit_occurred: true`
  - `live_second_narration_occurred: true`
  - `route_completed: true`
  - `matches_expected_first_spot: true`
  - `matches_expected_second_spot: true`

## Whether The Round Ended In `live_second_poi_enabled`, `live_second_poi_without_narration`, Or `live_second_progression_blocked`

This round ended in:

- `live_second_poi_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. decide whether this explicit isolated live-validation world should remain the accepted MVSim PC validation asset
2. if needed later, separate "truthful live bridge validation" from any higher-realism simulation track
3. avoid silently broadening the claim from "validated multistop asset" into "general autonomous simulator progression"

## Exact Validation Performed

### Probe validation

- `python scripts/print_mvsim_live_probe.py --config configs/sim.yaml`
- verified:
  - `runtime_available: true`
  - `live_pose_surface.topic_name: "/tour_bot/pose"`
  - `live_validation_alignment.strategy: "isolated_live_validation_world_with_forward_motion"`
  - `live_validation_alignment.motion_strategy: "constant_forward_velocity_along_demo_axis"`
  - `live_validation_alignment.target_spot_name: "East Gate"`
  - `live_validation_alignment.second_target_spot_name: "Central Plaza"`

### Focused unit validation

- `python -m unittest tests.test_mvsim_live_runtime -v`
  - passed
- `python -m unittest tests.test_mvsim_live_bridge -v`
  - passed
- `python -m unittest tests.test_sim_pose_ingress -v`
  - passed
- `python -m unittest tests.test_api_server -v`
  - passed
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed

### Full regression validation

- `python -m unittest discover -s tests`
  - passed
  - `Ran 116 tests ... OK`

### Real live smoke validation

- launched:
  - sim pose ingress server on `127.0.0.1:8100`
  - sim-profile API server on `127.0.0.1:8001`
- ran:
  - `python scripts/run_mvsim_live_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100 --sample-count 180`
- observed from `live_validation_summary`:
  - `live_pose_reached_stack: true`
  - `live_first_poi_hit_occurred: true`
  - `live_second_poi_hit_occurred: true`
  - `live_second_narration_occurred: true`
  - `recent_triggered_spot_ids: ["gate", "plaza", "gallery"]`
  - `recent_narrated_spot_ids: ["gate", "plaza", "gallery"]`
  - `route_completed: true`
  - `matches_expected_first_spot: true`
  - `matches_expected_second_spot: true`
- observed from API:
  - `route_completed = true`
  - `current_index = 3`
  - `last_pose = {"x": 9.075166702270508, "y": 0.5, "label": "tour_bot"}`
  - `last_narration_text` populated with the real `History Gallery` narration
- observed from UI surface:
  - `/debug` returned `200`

## Current Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 38]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_live_bridge_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `80de369c5fcad3803366630bc3133be44015aec2`

## Whether Files Are Staged And/Or Committed

- repo code/doc bundle for Round 036:
  - committed
- currently staged:
  - no
- `coordination/latest_result.md`:
  - updated locally after commit only
  - not staged
  - not committed

## Blockers, Risks, Or Remaining Gaps

- this round validates a truthful isolated live-validation asset, not broad autonomous simulator behavior
- the multistop proof currently depends on:
  - an explicit validation world
  - an explicit validation vehicle
  - a fixed `y=0.5` forward lane
- port `8000` was unavailable during validation, so API live smoke used `8001`
- `docs/DEV_WORKFLOW.md` still has a separate pre-existing local modification outside this round
- temp smoke directories remain untracked and were intentionally not included in the commit
