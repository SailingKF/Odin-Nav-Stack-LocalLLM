# MVSim Live Pose Bridge Baseline

## Purpose

This document defines the narrowest truthful live-pose bridge currently available from the Linux-side MVSim runtime into the existing Windows-side `sim_pose_ingress` flow.

The goal is not to redesign simulation transport.
The goal is to answer one precise question:

- what live pose/output surface can we actually consume from the running MVSim process today
- and can at least one real sample be relayed into the current tour stack

## Live Pose Surface Discovered In Round 034

The currently validated live pose surface is:

- MVSim CLI topic surface
- topic name:
  - `/tour_bot/pose`
- message type:
  - `mvsim_msgs.TimeStampedPose`
- observed publisher node:
  - `World`
- observed publication rate:
  - about `9.6 Hz`

The current repo-local world publishes this topic through:

- `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`

using:

- `<publish_pose_topic>/tour_bot/pose</publish_pose_topic>`
- `<publish_pose_period>0.10</publish_pose_period>`

## Exact Discovery Commands

After launching the repo-local world in Ubuntu/WSL:

```text
/root/round033-mvsim-build/bin/mvsim launch /mnt/c/Users/saili/Desktop/odin_nav_stack_local_llm_docs/content/sim/mvsim/worlds/odin_minimal_tour.world.xml --headless -v INFO
```

The live surface was inspected with:

```text
/root/round033-mvsim-build/bin/mvsim topic list --details
/root/round033-mvsim-build/bin/mvsim topic hz /tour_bot/pose
/root/round033-mvsim-build/bin/mvsim topic echo /tour_bot/pose
/root/round033-mvsim-build/bin/mvsim node list
```

Observed facts:

- `topic list --details`
  - found `/tour_bot/pose`
  - type `mvsim_msgs.TimeStampedPose`
- `topic hz /tour_bot/pose`
  - measured about `9.6 Hz`
- `topic echo /tour_bot/pose`
  - emitted repeated pose samples such as:
    - `objectId: "tour_bot"`
    - `x: -3`
    - `y: -1.5`
    - `yaw: 0`

## Current Bridge Shape

The minimal bridge path is:

1. Windows-side script invokes:
   - `wsl.exe -d Ubuntu -u root -- /root/round033-mvsim-build/bin/mvsim topic echo /tour_bot/pose`
2. the bridge parses the emitted `TimeStampedPose` text stream
3. parsed samples are converted into the repo's existing richer payload shape
4. the existing projection/normalization seam converts those into:
   - `{x, y, label}`
5. those poses are POSTed to the existing Windows-side `sim_pose_ingress` HTTP bridge

Current implementation:

- live source:
  - `services/sim_publisher_bridge/mvsim_live_source.py`
- runnable demo:
  - `scripts/run_mvsim_live_bridge_demo.py`

## Operator Demo Flow

Start sim ingress on Windows:

```text
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Optional API proxy for `/debug` observation:

```text
python scripts/run_api_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8000
```

Then run the live bridge demo:

```text
python scripts/run_mvsim_live_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100
```

The demo script:

- starts a fresh headless MVSim runtime in WSL unless `--attach-existing-runtime` is used
- subscribes to `/tour_bot/pose`
- relays a small batch of live samples into `sim_pose_ingress`
- prints payload samples plus resulting ingress/session state
- prints a `live_validation_summary` block with:
  - live pose relay status
  - whether a live POI hit occurred
  - whether a live narration event occurred
  - which spot was validated
  - the configured alignment strategy

## What Was Truthfully Validated

Round 035 validates these end-to-end facts:

- a real live `mvsim_msgs.TimeStampedPose` sample from the WSL MVSim runtime reached the current `sim_pose_ingress` path
- that live pose truthfully hit the first current POI
- that hit truthfully produced a live-triggered narration event

Observed live pose sample:

- `x = 0.0`
- `y = 0.0`
- `label = "tour_bot"`

Observed downstream fact in the current Windows-side runtime:

- `state.last_pose` became the relayed live pose sample
- `latest_session.latest_narration_text` became the generated `East Gate` narration
- `latest_session.latest_audio_playback.spot_name` became `East Gate`
- after the live hit, the next current route target became:
  - `active_spot_name = "Central Plaza"`

Chosen alignment strategy:

- keep the current demo POI content unchanged
- keep the current live bridge transport unchanged
- align the minimal repo-local MVSim world init pose to the first current POI
- record that choice in `configs/sim.yaml` under:
  - `mvsim_integration.live_validation_alignment`

What this does **not** prove yet:

- natural multi-POI live progression from continuous simulator motion
- full live route completion

So this baseline now proves truthful cross-boundary live pose relay, a truthful first live POI hit, and a truthful first live-triggered narration event.

## Scope Limits

This baseline does not yet claim:

- full route progression from live robot motion
- ROS 2 integration
- simulator redesign
- a packaged cross-boundary process supervisor

The current bridge is intentionally narrow:

- one real live topic
- one explicit parsing strategy
- one explicit relay path into existing ingress
