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

Then run the live bridge demo:

```text
python scripts/run_mvsim_live_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100
```

The demo script:

- starts a fresh headless MVSim runtime in WSL unless `--attach-existing-runtime` is used
- subscribes to `/tour_bot/pose`
- relays a small batch of live samples into `sim_pose_ingress`
- prints payload samples plus resulting ingress/session state

## What Was Truthfully Validated

Round 034 validated at least this end-to-end fact:

- a real live `mvsim_msgs.TimeStampedPose` sample from the WSL MVSim runtime reached the current `sim_pose_ingress` path

Observed live pose sample:

- `x = -3.0`
- `y = -1.5`
- `label = "tour_bot"`

Observed downstream fact in the current Windows-side runtime:

- `state.last_pose` became the relayed live pose sample
- the current route target remained:
  - `active_spot_name = "East Gate"`

What this does **not** prove yet:

- a live-driven POI trigger
- live-driven narration progression

Reason:

- the current repo-local MVSim world starts the robot at `(-3.0, -1.5)`
- the current demo POI content places `East Gate` at `(0.0, 0.0)`

So this baseline proves truthful cross-boundary live pose relay, but not yet live route completion.

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
