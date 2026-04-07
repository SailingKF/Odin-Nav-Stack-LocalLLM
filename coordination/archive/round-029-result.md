# Current Round Result

## Round
Round 029 - MVSim Minimal Integration And End-To-End Tour Validation Baseline

## Summary

- Status: PASSED
- The repository now contains a narrow MVSim-oriented compatibility path that drives the existing external sim-ingress HTTP contract and completes a full POI-triggered tour on PC.
- This round used a mixed approach:
  - real downstream HTTP/services/runtime behavior
  - MVSim-style planar observation compatibility scaffolding on the simulator side
- The current `/debug` path is now usable in `configs/sim.yaml` through an API proxy mode that observes the running sim-ingress runtime instead of spinning up a second mock tour runtime.

## What I Changed

- Added an MVSim-style simulator observation source:
  - `services/sim_publisher_bridge/mvsim_source.py`
- Added a sample MVSim-oriented planar pose stream:
  - `content/sim/demo_mvsim_pose_stream.yaml`
- Added a runnable PC demo bridge:
  - `scripts/run_mvsim_compat_bridge_demo.py`
- Extended the sim profile config with a narrow MVSim integration section:
  - `configs/sim.yaml`
- Extended the sim pose-ingress runtime/app with minimal control and follow-up question support:
  - `services/sim_pose_ingress/runtime.py`
  - `services/sim_pose_ingress/app.py`
- Extended the existing sim ingress HTTP client for proxy/control reuse:
  - `services/sim_publisher_bridge/http_client.py`
- Added a sim-aware API proxy mode so:
  - `python scripts/run_api_server.py --config configs/sim.yaml`
  now serves `/debug` while proxying to the running sim-ingress runtime
- Added focused MVSim/minimal-integration docs:
  - `docs/MVSIM_MINIMAL_INTEGRATION.md`
- Updated README with the new PC validation flow:
  - `README.md`
- Added focused tests:
  - `tests/test_mvsim_integration.py`
  - updated `tests/test_sim_pose_http_bridge.py`

## Exact Files Changed

- `README.md`
- `configs/sim.yaml`
- `content/sim/demo_mvsim_pose_stream.yaml`
- `docs/MVSIM_MINIMAL_INTEGRATION.md`
- `scripts/run_mvsim_compat_bridge_demo.py`
- `services/api_server/app.py`
- `services/api_server/runtime.py`
- `services/sim_pose_ingress/app.py`
- `services/sim_pose_ingress/runtime.py`
- `services/sim_publisher_bridge/http_client.py`
- `services/sim_publisher_bridge/mvsim_source.py`
- `tests/test_mvsim_integration.py`
- `tests/test_sim_pose_http_bridge.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Whether This Used Real MVSim Runtime, A Compatibility Shim, Or A Mixed Approach

Current result is a mixed approach.

### Real in this round

- real `uvicorn` processes for:
  - `scripts/run_sim_pose_ingress_server.py`
  - `scripts/run_api_server.py --config configs/sim.yaml`
- real HTTP calls through:
  - `GET /health`
  - `POST /runtime/start`
  - `POST /poses/batch`
  - `POST /stream/finish`
  - `GET /state`
  - `GET /session/latest`
  - `POST /tour/question`
- real downstream tour behavior:
  - POI triggering
  - narration flow
  - session logging
  - state/session inspection
  - `/debug` page load through the sim-profile API server

### Compatibility scaffolding in this round

- no live `mvsim` runtime was detected on this PC
- `Get-Command mvsim -ErrorAction SilentlyContinue`
  - returned no command
- the simulator-side path therefore uses:
  - MVSim-style planar observation playback from `content/sim/demo_mvsim_pose_stream.yaml`
  - conversion into the existing richer publisher payload shape
  - existing HTTP ingress posting

This is explicitly documented as:

- `source_kind: "mvsim_compatibility_shim"`

So this round is not claiming a direct live MVSim process adapter yet.

## Exact Commands Used To Run The PC Validation

### Service startup

```text
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
python scripts/run_api_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8000
```

### MVSim-oriented bridge playback

```text
python scripts/run_mvsim_compat_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100
```

### Manual verification calls

```text
Invoke-RestMethod -Uri 'http://127.0.0.1:8100/health'
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health'
Invoke-WebRequest -Uri 'http://127.0.0.1:8000/debug'
Invoke-RestMethod -Uri 'http://127.0.0.1:8100/state'
Invoke-RestMethod -Uri 'http://127.0.0.1:8100/session/latest'
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/tour/question' -ContentType 'application/json' -Body '{"question":"What does this final stop prove?"}'
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/session/latest'
```

## What End-To-End Behavior Was Verified

Verified on PC:

- the MVSim-oriented publisher/runner started from a planar observation file
- the real external sim-ingress runtime started through `/runtime/start`
- a real batch of normalized `x/y/label` poses was posted through `/poses/batch`
- the stream was explicitly closed through `/stream/finish`
- the sim-driven route hit all three demo POIs:
  - `East Gate`
  - `Central Plaza`
  - `History Gallery`
- the downstream state reached:
  - `route_completed: true`
- the session log captured the final tour run at:
  - `session_logs/sim/mock_tour_20260406T024046Z.jsonl`
- the sim-profile API server exposed `/debug`
- the sim-profile API proxy answered a follow-up question against the last narrated POI:
  - `What does this final stop prove?`

## What APIs And Services Were Exercised

### Services exercised

- sim pose ingress server
- sim-profile API server in proxy mode
- MVSim-oriented publisher bridge demo

### API surfaces exercised

On sim ingress:

- `GET /health`
- `POST /runtime/start`
- `POST /poses/batch`
- `POST /stream/finish`
- `GET /state`
- `GET /session/latest`

On API proxy/debug server:

- `GET /health`
- `GET /debug`
- `GET /state`
- `GET /session/latest`
- `POST /tour/question`

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_mvsim_integration -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_sim_pose_http_bridge -v`
  - passed
  - `Ran 4 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 99 tests ... OK`

Focused coverage now includes:

- MVSim-style planar observation conversion
- MVSim YAML source playback
- end-to-end bridge run against the sim ingress app
- sim-profile API proxy access to state/session/question surfaces
- `/debug` availability in the sim-profile API path

### Manual

Ran real PC processes for:

- `run_sim_pose_ingress_server.py`
- `run_api_server.py --config configs/sim.yaml`

Confirmed:

- `http://127.0.0.1:8100/health`
  - returned `service: "sim-pose-ingress-runtime"`
- `http://127.0.0.1:8000/health`
  - returned `service: "tour-api-sim-proxy"`
  - returned `api_mode: "sim_ingress_proxy"`
- `http://127.0.0.1:8000/debug`
  - returned `200`
- `python scripts/run_mvsim_compat_bridge_demo.py ...`
  - produced `source_kind: "mvsim_compatibility_shim"`
  - posted 4 planar observations
- `http://127.0.0.1:8100/state`
  - showed:
    - `route_completed: true`
    - `current_index: 3`
    - `last_narration_text` for `History Gallery`
- `http://127.0.0.1:8100/session/latest`
  - showed:
    - `session_id: "mock_tour_20260406T024046Z"`
    - `latest_narration_text` for `History Gallery`
- `POST http://127.0.0.1:8000/tour/question`
  - returned:
    - `spot_name: "History Gallery"`
    - `answer_text: "It proves that the route can finish cleanly after several narrations without duplicate triggers."`

I also stopped the temporary manual-validation Python server processes after verification.

## What MVSim-Oriented Integration Surface Now Exists

Current MVSim-oriented seam now consists of:

- `services/sim_publisher_bridge/mvsim_source.py`
  - converts MVSim-style `pose2d`/`velocity2d` observations into the existing richer publisher payload shape
- `content/sim/demo_mvsim_pose_stream.yaml`
  - sample planar wheeled-robot observation playback
- `scripts/run_mvsim_compat_bridge_demo.py`
  - engineer-facing PC validation runner
- sim-profile API proxy mode in:
  - `services/api_server/runtime.py`
  so `/debug` can observe the real sim-ingress runtime instead of another local mock runtime

## What Still Remains Before Map-Format Work Or ROS-Side Integration Should Start

- a direct live MVSim process/runtime adapter if we later decide we need it
- explicit MVSim world/map binding rather than a static observation playback file
- richer timing/clock semantics if simulator pacing becomes important
- ROS-side formal integration
- map-format or occupancy-map design

This round intentionally stops before all of those.

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 30]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `5418486c7bdd20ce330566461bb9d34be8802e3c`

## Staged / Committed State

- Round 029 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule

## Blockers, Risks, Or Remaining Gaps

- No live `mvsim` binary/runtime is wired yet on this PC; this round therefore uses a clearly labeled compatibility shim instead of direct runtime attachment.
- The current MVSim path is planar pose playback only. It does not yet model richer simulator timing, wheel physics, or map coupling.
- The sim-profile API server is currently a thin proxy for observation/debugging, not a separate sim-control orchestrator.
- This round intentionally stops before Isaac, ROS formalization, map-format work, or packaging.
