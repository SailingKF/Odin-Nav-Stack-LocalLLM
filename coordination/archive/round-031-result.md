# Current Round Result

## Round
Round 031 - MVSim Live Runtime And Minimal World Bring-Up Baseline

## Summary

- Status: BLOCKER, NARROWLY REPORTED
- This round did **not** validate a real live MVSim process driving the tour stack on this PC.
- The repository now contains:
  - a repo-local minimal MVSim world asset
  - a repo-local minimal vehicle definition
  - a live-runtime probe surface
  - operator-visible mode distinction between:
    - `live_mvsim_runtime`
    - `mvsim_compatibility_shim`
- The real blocker on this PC is:
  - no `mvsim` executable was found

This means the round completed in **blocker state**, not live mode and not fake compatibility fallback.

## What I Changed

- Added live-runtime probing utilities:
  - `services/sim_publisher_bridge/mvsim_live.py`
- Added an operator-facing CLI probe:
  - `scripts/print_mvsim_live_probe.py`
- Added a repo-local minimal MVSim vehicle definition:
  - `content/sim/mvsim/definitions/odin_tour_bot.vehicle.xml`
- Added a repo-local minimal MVSim world:
  - `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`
- Extended `configs/sim.yaml` to make the intended live-runtime contract explicit:
  - `mvsim_integration.executable`
  - `mvsim_integration.world_file`
- Extended the MVSim validation harness runtime and page so operators can now see:
  - configured MVSim mode
  - effective MVSim mode
  - live-runtime availability
  - compatibility source readiness
- Added focused tests for:
  - live-runtime probing
  - live-mode blocker handling inside the harness
- Added/updated focused docs:
  - `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
  - `docs/MVSIM_MINIMAL_INTEGRATION.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`
- Updated README with the new live-runtime baseline and blocker semantics

## Exact Files Changed

- `README.md`
- `configs/sim.yaml`
- `content/sim/mvsim/definitions/odin_tour_bot.vehicle.xml`
- `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`
- `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- `docs/MVSIM_MINIMAL_INTEGRATION.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `scripts/print_mvsim_live_probe.py`
- `services/mvsim_validation_harness/runtime.py`
- `services/mvsim_validation_harness/static/index.html`
- `services/sim_publisher_bridge/mvsim_live.py`
- `tests/test_mvsim_live_runtime.py`
- `tests/test_mvsim_validation_harness.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Whether A Real `mvsim` Runtime Was Found On This PC

No.

Observed checks:

- `Get-Command mvsim -ErrorAction SilentlyContinue`
  - no command returned
- `where.exe mvsim`
  - returned:
    - `INFO: Could not find files for the given pattern(s).`
- recursive local search for `mvsim.exe` in common Windows locations
  - no result found

## Whether The Round Completed In Live Mode, Compatibility Mode Fallback, Or Blocker State

This round completed in:

- `blocker_state`

Specifically:

- live mode was **not** validated
- compatibility mode was **not** used to fake live success
- the blocker was reported explicitly as:
  - `mvsim_executable_not_found`

## What Minimal World Asset Now Exists

The repo now contains a minimal MVSim bring-up asset:

- world:
  - `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`
- vehicle:
  - `content/sim/mvsim/definitions/odin_tour_bot.vehicle.xml`

Characteristics:

- one small differential wheeled robot
- simple bounded floor
- a few walls for scene structure
- no ROS dependence
- intended as bring-up scaffolding, not final simulation architecture

## How Live Simulator Pose Is Turned Into The Existing Tour Path

Current truthful state:

- it is **not yet turned into the existing tour path on this PC**
- the round stops before that conversion because no real `mvsim` runtime is available

What exists now:

- a live-runtime probe and launch-command surface
- a world asset and vehicle asset prepared for live bring-up
- explicit operator-mode distinction between live and compatibility paths

What still remains for a true live path:

- a real installed `mvsim` runtime
- validated knowledge of the best live pose output seam from that runtime into the current sim-ingress path
- one true end-to-end live process run

So this round does **not** claim a live pose bridge was already proven.

## How The Harness / Operator Can Tell Live Vs Compatibility Mode

The harness now surfaces:

- `Configured MVSim Mode`
- `Effective MVSim Mode`
- `Live Runtime Available`
- `Live MVSim Runtime`
- `Compatibility Source`

Behavior now is:

- if config stays at `compatibility_shim`
  - the harness shows:
    - configured mode `compatibility_shim`
    - effective mode `compatibility_shim`
    - compatibility observation source readiness
- if config switches to `live_runtime` and `mvsim` is missing
  - the harness returns:
    - `status: "blocked_live_runtime_unavailable"`
    - `mvsim_mode: "blocked_live_runtime"`
    - blocker detail explaining that the executable was not found

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_mvsim_live_runtime -v`
  - passed
  - `Ran 2 tests ... OK`
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest tests.test_mvsim_integration -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 107 tests ... OK`

### Manual

#### Probe current sim profile

Command:

```text
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
```

Observed result:

- `configured_mode: "compatibility_shim"`
- `effective_mode: "compatibility_shim"`
- `live_runtime.runtime_available: false`
- `live_runtime.world_file_exists: true`
- `compatibility_source.source_kind: "mvsim_compatibility_shim"`

#### Force live mode and verify blocker behavior

Used a temporary config derived from `configs/sim.yaml` with:

- `mvsim_integration.mode = live_runtime`
- `mvsim_integration.executable = definitely_missing_mvsim_binary`

Then invoked:

- `MVSimValidationHarnessRuntime(...).run_validation()`

Observed result:

- `status: "blocked_live_runtime_unavailable"`
- `mvsim_mode: "blocked_live_runtime"`
- blocker detail:
  - `configured live MVSim executable 'definitely_missing_mvsim_binary' was not found on this PC`

#### Check operator-facing harness status surface

Command:

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim.yaml --host 127.0.0.1 --port 8311
```

Then queried:

```text
GET http://127.0.0.1:8311/status
```

Observed result included:

- `mvsim_mode_summary.configured_mode: "compatibility_shim"`
- `mvsim_mode_summary.effective_mode: "compatibility_shim"`
- `mvsim_mode_summary.live_runtime.runtime_available: false`
- `mvsim_mode_summary.live_runtime.world_file_exists: true`
- `mvsim_mode_summary.compatibility_source.source_kind: "mvsim_compatibility_shim"`

## Exact Commands Used

```text
where.exe mvsim
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
python -m unittest tests.test_mvsim_live_runtime -v
python -m unittest tests.test_mvsim_validation_harness -v
python -m unittest tests.test_mvsim_integration -v
python -m unittest tests.test_api_server -v
python -m unittest discover -s tests
python scripts/run_mvsim_validation_harness.py --config configs/sim.yaml --host 127.0.0.1 --port 8311
GET http://127.0.0.1:8311/status
```

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 32]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
```

## Commit Hash

- `53242805685764761b0e514fc48457415ac62661`

## Staged / Committed State

- Round 031 code bundle: committed
- no files remain staged
- `coordination/latest_result.md`: updated locally after commit, not staged
- unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule
- untracked `tmp_mvsim_harness_smoke/` remains outside this commit

## Blockers, Risks, Or Remaining Gaps Before Map-Format Or ROS Work

- The real blocker is still first-order and external:
  - no usable `mvsim` runtime is installed on this PC
- Because of that, this round does **not** prove:
  - live simulator pose extraction
  - live simulator pose posting into sim-ingress
  - full live end-to-end tour completion
- The current live world/vehicle assets are prepared but unvalidated against a real runtime on this machine.
- The operator harness now distinguishes live vs compatibility mode correctly, but one manual environment wrinkle also appeared during status probing:
  - `api_server` on port `8000` may attach to an unrelated existing local process if that port is already occupied
  - this is separate from the MVSim blocker, but worth remembering in later rounds

This round intentionally stopped before ROS formalization, simulator redesign, or map-format work.
