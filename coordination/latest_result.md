# Current Round Result

## Round
Round 051 - Interactive Single-Operator Manual Review Mode

## Goal
Turn the MVSim GUI review path into a practical single-operator flow on this PC by fixing the `/debug` default API target, removing the 3-terminal happy-path burden, and switching the review mode to deliberate manual movement instead of auto-running to completion.

## Summary

- Status: `interactive_manual_review_mode_ready`
- The round fixes the `/debug` defaulting problem for the current `8001` sim-profile flow.
- The round upgrades `scripts/run_mvsim_gui_review.py` into a one-command operator entrypoint that starts:
  - `sim_pose_ingress_server`
  - the sim-profile API server
  - the MVSim GUI runtime
  - a continuous live-pose relay into `sim_pose_ingress`
- The round adds a separate manual-review config and world so the robot no longer auto-drives in this mode.
- A real end-to-end review attempt was made on this machine.
- The robot started stationary in the manual-review world.
- The robot was then moved through the same GUI keyboard-control path used by a human operator, and a real `East Gate` POI/narration trigger was observed in the existing Windows-side stack.

## Exact Files Changed

- `services/api_server/static/index.html`
- `services/sim_publisher_bridge/http_client.py`
- `services/sim_publisher_bridge/mvsim_live_source.py`
- `scripts/run_mvsim_gui_review.py`
- `scripts/run_mvsim_live_bridge_stream.py`
- `configs/sim_harness_manual_review.yaml`
- `content/sim/mvsim/worlds/odin_manual_review_tour.world.xml`
- `docs/MVSIM_LIVE_POSE_BRIDGE.md`
- `tests/test_api_server.py`
- `tests/test_mvsim_live_bridge.py`
- `coordination/latest_result.md`

## What Changed

- `/debug` UI fix:
  - the page no longer hardcodes `http://127.0.0.1:8000` into the input field
  - `initialBaseUrl()` now prefers `window.location.origin`
  - if an old saved loopback URL still points to `8000`, the page upgrades it to the current page origin instead of silently reusing the stale value
- Single-command launcher:
  - `scripts/run_mvsim_gui_review.py` now starts the local review stack instead of only printing follow-up commands
  - the launcher auto-attaches to healthy local `8110` / `8001` services when they already exist
  - otherwise it starts those services itself and waits for health before launching the GUI runtime and continuous bridge
- Manual-review runtime path:
  - added `configs/sim_harness_manual_review.yaml`
  - added `content/sim/mvsim/worlds/odin_manual_review_tour.world.xml`
  - the manual-review world uses the existing stationary `odin_tour_bot.vehicle.xml`
  - the manual-review world starts at `(-2.0, 0.5, 0.0)` so the operator must deliberately move into the first POI instead of spawning on a completed or auto-running path
- Continuous live pose relay:
  - added `scripts/run_mvsim_live_bridge_stream.py`
  - added single-pose ingest support in the HTTP client
  - updated the MVSim live source parser to support incremental streaming instead of only finite batch parsing
- Docs/tests:
  - updated the GUI manual review instructions in `docs/MVSIM_LIVE_POSE_BRIDGE.md`
  - updated tests to cover the `/debug` defaulting change and the incremental pose parser

## Round Shape

- New launcher: no
- Updated launcher: yes
- New manual-review config/world asset: yes
- `/debug` UI fix: yes
- Docs updated: yes

## Exact Single-Command Review Entrypoint

```text
python scripts/run_mvsim_gui_review.py --config configs/sim_harness_manual_review.yaml --open-browser
```

The same command without `--open-browser` was also validated during this round:

```text
python scripts/run_mvsim_gui_review.py --config configs/sim_harness_manual_review.yaml
```

## `/debug` Behavior Before And After

Before this round:

- the page hardcoded `http://127.0.0.1:8000`
- the current `sim_harness` operator path actually served from `http://127.0.0.1:8001`
- the observed human result was:
  - `Request failed: Failed to fetch`
  - until the operator manually corrected the URL

After this round:

- the page input no longer ships with a hardcoded `8000` value
- the page defaults to `window.location.origin`
- old saved loopback values of:
  - `http://127.0.0.1:8000`
  - `http://localhost:8000`
  are upgraded to the current page origin when the page is now served from a different loopback port
- fetching `http://127.0.0.1:8001/debug` succeeded with `200`

## Exact Manual-Review Launch Commands Attempted

```text
wsl.exe --shutdown
python scripts/run_mvsim_gui_review.py --config configs/sim_harness_manual_review.yaml
Invoke-WebRequest http://127.0.0.1:8110/health
Invoke-WebRequest http://127.0.0.1:8001/health
Invoke-WebRequest http://127.0.0.1:8001/debug
Invoke-WebRequest http://127.0.0.1:8110/state
Invoke-WebRequest http://127.0.0.1:8110/session/latest
```

To exercise the same keyboard-control path programmatically from this terminal-only executor session, the review also used:

```text
$wshell = New-Object -ComObject WScript.Shell
$wshell.AppActivate('mvsim')
1..18 | ForEach-Object { $wshell.SendKeys('w'); Start-Sleep -Milliseconds 150 }
1..45 | ForEach-Object { $wshell.SendKeys('w'); Start-Sleep -Milliseconds 120 }
```

## Exact Observed Result Of Single-Command Bring-Up

- `scripts/run_mvsim_gui_review.py` brought up:
  - `sim_pose_ingress_server` on `http://127.0.0.1:8110`
  - the sim-profile API server on `http://127.0.0.1:8001`
  - the MVSim GUI runtime using:
    - `content/sim/mvsim/worlds/odin_manual_review_tour.world.xml`
  - the continuous bridge process:
    - `scripts/run_mvsim_live_bridge_stream.py --config configs/sim_harness_manual_review.yaml --base-url http://127.0.0.1:8110`
- the launcher printed:
  - `Interactive MVSim manual review stack is running.`
  - `Debug page: http://127.0.0.1:8001/debug`
- `Invoke-WebRequest http://127.0.0.1:8110/health` succeeded
- `Invoke-WebRequest http://127.0.0.1:8001/health` succeeded
- `Invoke-WebRequest http://127.0.0.1:8001/debug` returned `200`

## Manual-Control And POI Trigger Truth

Before any keyboard input:

- `state.is_running = true`
- `route_completed = false`
- `last_pose = {"x": -2.0, "y": 0.5, "label": "tour_bot"}`
- `latest_narration_text = null`
- `recent_poi_triggers = []`
- the robot did not auto-run forward on its own in this mode

After a first small `W` key sequence:

- `last_pose.x` moved from `-2.0` to about `-1.4979`
- this confirmed that the manual-review world accepted the GUI keyboard control path

After a longer `W` key sequence:

- `current_index = 1`
- `active_spot_name = "Central Plaza"`
- `latest_triggered_spot_id = "gate"`
- `latest_triggered_spot_name = "East Gate"`
- `latest_narrated_spot_id = "gate"`
- `latest_narrated_spot_name = "East Gate"`
- `latest_narration_text` became:
  - `Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI.`
- `recent_poi_triggers` recorded `East Gate`
- `recent_narrations` recorded `East Gate`

So this round truthfully observed:

- a non-auto-run manual-review world
- actual GUI-driven movement
- at least one real POI trigger
- at least one real narration trigger

## Control Method Used For Movement

- MVSim GUI keyboard controls on the selected `tour_bot`
- terminal-side validation used Windows `WScript.Shell` `AppActivate('mvsim')` plus repeated `SendKeys('w')` calls to exercise the same operator keyboard path in a terminal-only executor environment

## Existing Automated / Headless Path Recheck

Rechecked:

```text
python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml
```

Observed:

- `configured_mode = "live_runtime"`
- `effective_mode = "live_runtime"`
- `runtime_available = true`
- `blocker = null`

The automated/headless validation path remains available.

## Validation Performed

- `python -m unittest tests.test_api_server tests.test_mvsim_live_bridge -v`
- `python -m unittest tests.test_mvsim_validation_harness tests.test_mvsim_validation_reporting -v`
- `python scripts/run_mvsim_gui_review.py --help`
- `python scripts/run_mvsim_live_bridge_stream.py --help`
- `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml`
- real single-command bring-up with:
  - `python scripts/run_mvsim_gui_review.py --config configs/sim_harness_manual_review.yaml`
- health/debug checks via `Invoke-WebRequest`
- state/session verification before and after GUI keyboard movement
- GUI keyboard-path movement via `WScript.Shell` `AppActivate + SendKeys`
- final teardown via:
  - `Stop-Process ...`
  - `wsl.exe --shutdown`

## Acceptance Criteria Check

- the round fixes the `/debug` default API target for the current `sim_harness` operator flow: yes
- the round provides one repo-owned single-command manual review entrypoint: yes
- that manual review mode starts the required local stack without the operator manually composing the previous 3-command happy path: yes
- the manual review mode uses a non-auto-run robot behavior: yes
- the operator can manually move the robot in the GUI and at least one real POI/narration can be triggered: yes
- the existing automated/headless validation path still works or was truthfully rechecked: yes
- `coordination/latest_result.md` is updated with exact commands, observations, and blocker state: yes

## Reviewer-Subagent Conclusion

- Reviewer result: `PASS`
- Reviewer notes:
  - Round 051 requirements are met.
  - Remaining risk is limited to operator-feel ergonomics and the fact that this terminal-only validation used `SendKeys` to exercise the same GUI keyboard path before a direct human hands-on pass.
  - No scope drift remains in the executor commit scope once owner-side coordination files are excluded.

## Round Outcome

- This round ended in:
  - `interactive_manual_review_mode_ready`

## Recommended Human Review Steps

1. Run:
   - `python scripts/run_mvsim_gui_review.py --config configs/sim_harness_manual_review.yaml --open-browser`
2. Wait for:
   - `Interactive MVSim manual review stack is running.`
3. Focus the MVSim window and keep `tour_bot` selected.
4. Use:
   - `W` / `S` to move
   - `A` / `D` to turn
   - `Space` to stop
5. Watch `/debug` on:
   - `http://127.0.0.1:8001/debug`
6. Confirm at least:
   - `latest_narration_text` updates after entering `East Gate`
   - `recent_poi_triggers` records `East Gate`
   - no manual API URL correction is needed on `/debug`

## Blockers / Risks / Remaining Gaps

- the terminal-only executor validated the GUI control path through `AppActivate + SendKeys`; a human should still perform a direct hands-on pass for product feel and camera/operator ergonomics
- `scripts/run_mvsim_gui_review.py` starts child services directly but does not yet maintain a richer supervisor UI or restart policy, which remains intentionally out of scope

## Git Delivery Status

- Branch: `main`
- Current `git status --short --branch` after the implementation commit and before staging this result file:

```text
## main...origin/main [ahead 1]
 M coordination/latest_prompt.md
 M coordination/latest_result.md
?? coordination/archive/round-050-prompt.md
?? coordination/archive/round-050-result.md
```

- Implementation commit hash:
  - `5015b74c82b9fd866b3530447b6d6246356b3ef1`
- Implementation commit message:
  - `feat: add interactive MVSim manual review mode`
- Files staged:
  - not yet, for this result-file update
- Files committed:
  - yes, the implementation bundle has already been committed
- Push succeeded: pending
