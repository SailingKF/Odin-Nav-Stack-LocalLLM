# Current Round Result

## Round
Round 034 - MVSim Live Pose Surface Discovery And Minimal Bridge Baseline

## Summary

- Status: `live_pose_bridge_enabled`
- This round moved beyond "MVSim launches in WSL" and identified a real live pose surface from the running Linux-side simulator.
- The discovered surface is:
  - topic: `/tour_bot/pose`
  - type: `mvsim_msgs.TimeStampedPose`
  - observed publisher: `World`
  - observed rate: about `9.6 Hz`
- A minimal live bridge now exists from that WSL-side pose stream into the existing Windows-side `sim_pose_ingress` HTTP path.
- The truthful end-to-end fact validated in this round is:
  - a real live MVSim pose sample reached the current Windows-side sim-ingress runtime and appeared as `state.last_pose`

## What I Changed

- Added a live pose source for the current WSL MVSim topic-echo surface:
  - `services/sim_publisher_bridge/mvsim_live_source.py`
- Added a runnable operator demo that:
  - launches or attaches to the WSL MVSim runtime
  - samples live `/tour_bot/pose`
  - relays those samples into the existing Windows-side sim-ingress bridge
  - `scripts/run_mvsim_live_bridge_demo.py`
- Extended the live runtime probe/config surface so operator tooling can show the discovered live pose topic and bridge mode:
  - `services/sim_publisher_bridge/mvsim_live.py`
  - `configs/sim.yaml`
- Updated the validation harness surface so operators can see:
  - `Live Pose Topic`
  - `Live Bridge Mode`
  - `services/mvsim_validation_harness/static/index.html`
- Added focused tests for:
  - parsing real `mvsim topic echo` output
  - live-pose-shaped relay into sim-ingress
  - updated live probe surface
  - `tests/test_mvsim_live_bridge.py`
  - `tests/test_mvsim_live_runtime.py`
- Added and updated focused docs:
  - `docs/MVSIM_LIVE_POSE_BRIDGE.md`
  - `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`
  - `README.md`

## Exact Files Changed

- `README.md`
- `configs/sim.yaml`
- `docs/MVSIM_LIVE_POSE_BRIDGE.md`
- `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `scripts/run_mvsim_live_bridge_demo.py`
- `services/mvsim_validation_harness/static/index.html`
- `services/sim_publisher_bridge/mvsim_live.py`
- `services/sim_publisher_bridge/mvsim_live_source.py`
- `tests/test_mvsim_live_bridge.py`
- `tests/test_mvsim_live_runtime.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## What Live Pose / Output Surface Was Discovered

The currently validated live pose/output surface is MVSim's built-in CLI topic surface.

Observed topic:

- `/tour_bot/pose`

Observed type:

- `mvsim_msgs.TimeStampedPose`

Observed node list:

- `World`
- `anonymous`

Observed publication rate:

- about `9.6 Hz`

Observed sample payload fields from `topic echo`:

- `unixTimestamp`
- `objectId`
- `pose.x`
- `pose.y`
- `pose.z`
- `pose.yaw`

Observed sample:

```text
objectId: "tour_bot"
pose {
  x: -3
  y: -1.5
  z: 0
  yaw: 0
  pitch: 0
  roll: 0
}
```

## Exact Commands Used To Inspect Or Consume That Surface

### Runtime launch in WSL

```text
/root/round033-mvsim-build/bin/mvsim launch /mnt/c/Users/saili/Desktop/odin_nav_stack_local_llm_docs/content/sim/mvsim/worlds/odin_minimal_tour.world.xml --headless -v INFO
```

### Surface discovery commands

```text
/root/round033-mvsim-build/bin/mvsim topic list --details
/root/round033-mvsim-build/bin/mvsim topic hz /tour_bot/pose
/root/round033-mvsim-build/bin/mvsim topic echo /tour_bot/pose
/root/round033-mvsim-build/bin/mvsim node list
```

### Repo-local operator probe

```text
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
```

### Minimal bridge demo

Start sim ingress:

```text
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Run the live bridge:

```text
python scripts/run_mvsim_live_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100 --sample-count 3
```

## Whether A Minimal Live Bridge Into `sim_pose_ingress` Now Works

Yes.

The current minimal bridge path is:

1. Windows-side script launches or attaches to the WSL runtime
2. Windows calls:
   - `wsl.exe -d Ubuntu -u root -- /root/round033-mvsim-build/bin/mvsim topic echo /tour_bot/pose`
3. the text stream is parsed into the repo's richer simulator payload shape
4. existing projection + normalization seams convert that into:
   - `{x, y, label}`
5. those poses are POSTed to the current Windows-side `sim_pose_ingress` HTTP bridge

This bridge is implemented through:

- `services/sim_publisher_bridge/mvsim_live_source.py`
- `scripts/run_mvsim_live_bridge_demo.py`

## What End-To-End Live Fact Was Actually Validated

The truthful end-to-end fact validated in this round is:

- a real live `mvsim_msgs.TimeStampedPose` sample from the WSL MVSim runtime reached the current Windows-side sim-ingress runtime

Observed live sample:

- `x = -3.0`
- `y = -1.5`
- `label = "tour_bot"`

Observed downstream state fact:

- `state.last_pose == {"x": -3.0, "y": -1.5, "label": "tour_bot"}`

Observed route-state fact:

- `active_spot_name == "East Gate"`

This proves the cross-boundary relay is real.

What it does **not** prove yet:

- live POI trigger
- live narration start
- live route completion

Reason:

- the current MVSim world starts the robot at `(-3.0, -1.5)`
- the current demo POI content places `East Gate` at `(0.0, 0.0)`

So the live pose now reaches the route runtime truthfully, but the current world/POI alignment is not yet sufficient for a live POI hit.

## Whether The Round Ended In `live_pose_bridge_enabled`, `live_pose_surface_found_but_bridge_blocked`, Or `live_pose_surface_blocked`

This round ended in:

- `live_pose_bridge_enabled`

## What The Next Narrow Step Is After This

The next narrow step is:

1. align the current live MVSim path with a route/POI contract that can truthfully produce a live POI hit
2. or adjust the minimal world / POI mapping so the first live runtime pose progression can trigger a current POI
3. then validate one live-driven narration event before broadening into richer bridge/runtime work

This is now a world/route-alignment and live progression question, not a base live-pose extraction question.

## Exact Validation Performed

### Surface discovery

- real WSL runtime launched
- `mvsim topic list --details`
  - found `/tour_bot/pose`
  - type `mvsim_msgs.TimeStampedPose`
- `mvsim topic hz /tour_bot/pose`
  - measured about `9.6 Hz`
- `mvsim topic echo /tour_bot/pose`
  - emitted repeated pose samples with `objectId`, `x`, `y`, and `yaw`
- `mvsim node list`
  - found nodes `World` and `anonymous`

### Focused tests

- `python -m unittest tests.test_mvsim_live_bridge -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_mvsim_live_runtime -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed
  - `Ran 6 tests ... OK`

### Full test sweep

- `python -m unittest discover -s tests`
  - passed
  - `Ran 114 tests ... OK`

### Real bridge demo

- started:
  - `python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100`
- ran:
  - `python scripts/run_mvsim_live_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100 --sample-count 3`
- observed:
  - demo exit code `0`
  - `state.last_pose` updated to the live relayed sample
  - `route_completed: false`
  - `last_narration_text: null`

## Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 36]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `c763de62d3bde62e8455741d0088bdd08ea8d30a`

## Whether Files Are Staged And / Or Committed

- Round 034 repo changes: committed
- no files remain staged
- `coordination/latest_result.md`: updated locally after commit, not staged
- unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule
- temporary runtime-attempt folders remain untracked and outside this commit

## Blockers, Risks, Or Remaining Gaps

- The live bridge currently depends on parsing `mvsim topic echo` text output
  - this is intentionally narrow and truthful, but not yet the most durable transport possible
- The validated live runtime still lives in WSL, not on the Windows PATH
- There is still no Windows-native `mvsim.exe`
- The current live world pose stream is static around `(-3.0, -1.5)` in the minimal world bring-up asset
- Current POI coordinates do not yet align with that live start pose, so this round did not validate a live POI trigger or narration
- WSL still emits a benign NAT/proxy warning on startup
  - this did not block live topic inspection or the minimal bridge
