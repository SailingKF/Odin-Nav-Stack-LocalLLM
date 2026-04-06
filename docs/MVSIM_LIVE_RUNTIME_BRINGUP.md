# MVSim Live Runtime Bring-Up Baseline

## Purpose

This document defines the narrow live-runtime bring-up surface introduced in Round 031.

The goal is not to redesign simulation.
The goal is to answer one precise question:

- can a real local `mvsim` process on this PC be detected and prepared for the current tour-validation stack?

If the answer is no, this document also defines how that blocker is surfaced without pretending the live path already works.

## What Now Exists

Repository-owned live-runtime preparation now includes:

- live-runtime probing:
  - `services/sim_publisher_bridge/mvsim_live.py`
- operator-facing probe script:
  - `scripts/print_mvsim_live_probe.py`
- a repo-local minimal MVSim vehicle definition:
  - `content/sim/mvsim/definitions/odin_tour_bot.vehicle.xml`
- a repo-local minimal MVSim world:
  - `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`

## Current Config Surface

Current `configs/sim.yaml` now makes the intended live-runtime contract explicit:

- `mvsim_integration.mode`
- `mvsim_integration.executable`
- `mvsim_integration.world_file`
- `mvsim_integration.observation_file`
- `mvsim_integration.vehicle_name`
- `mvsim_integration.assumed_frame_id`

Meaning:

- `mode: compatibility_shim`
  - use the existing observation-playback path
- `mode: live_runtime`
  - require a real local `mvsim` executable
  - require the configured world file
  - do **not** silently claim success if the runtime is missing

## Repo-Local Minimal World Asset

The minimal world is intentionally simple:

- one small differential wheeled robot
- one bounded rectangular floor
- a few walls to give the scene shape
- no ROS dependence
- no sensor simulation requirement

Files:

- `content/sim/mvsim/definitions/odin_tour_bot.vehicle.xml`
- `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`

This is a bring-up asset, not a final map-format decision.

## How The Operator Checks Live Readiness

Run:

```text
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
```

This reports:

- configured mode
- effective mode
- whether a real `mvsim` executable was found
- whether the configured world file exists
- the launch command that would be used
- the current blocker, if any

## How The Validation Harness Surfaces It

The MVSim validation harness now shows:

- `Configured MVSim Mode`
- `Effective MVSim Mode`
- `Live Runtime Available`
- `Live MVSim Runtime`
- `Compatibility Source`

This makes it obvious whether the operator is:

- running the compatibility shim
- ready for live runtime bring-up
- blocked on a missing `mvsim` runtime

## Current Limitation In This Round

On this PC, the live-runtime blocker is:

- no `mvsim` executable was found on PATH
- no `mvsim.exe` was found in the common Windows locations checked during validation

Therefore this round stops in a real blocker state for live mode instead of faking a live end-to-end run.

## Round 031 Retry Findings

The retry round pushed the environment blocker further and made the installation path more concrete.

### Runtime discovery findings on this PC

- `where.exe mvsim`
  - returned no executable
- `winget search mvsim`
  - no package found
- `winget search mrpt`
  - no package found
- `choco search mvsim --exact`
  - no package found
- `choco search mrpt`
  - no package found
- `wsl.exe --status`
  - reported that WSL is not installed on this PC

### Source-build findings on this PC

What is available:

- `git`
- `cmake`
- Visual Studio Community 2022
- MSVC toolchain through `VsDevCmd.bat`

What failed:

- direct `git clone` of `https://github.com/MRPT/mvsim.git`
  - failed with network resets / connect failures to GitHub over git HTTPS
- configuring `mvsim` from a downloaded source zip
  - failed because `mrpt-maps` and related MRPT packages were not installed
- configuring MRPT from its release source zip
  - progressed further, but failed because the source release did not contain required submodule content such as the embedded `glfw` / `nanoflann` sources expected by that build path

### What this means

The blocker is now more precise than “runtime missing”.

Current real blocker chain is:

1. no packaged `mvsim` runtime is available on this Windows PC via the package managers we checked
2. WSL is not installed, so the practical Linux path is not immediately available
3. source-build fallback is currently blocked by:
   - missing MRPT install
   - GitHub git transport instability for recursive source retrieval
   - incomplete dependency content in downloaded source zips for a clean Windows-from-source path

So the next enablement step is not a repo refactor.
It is an environment step:

- either install WSL and use the Linux MVSim/MRPT path
- or establish a reliable Windows source-build workflow with full git/submodule access and MRPT built first

## Exact Blocker Behavior

When `mvsim_integration.mode` is set to `live_runtime` and the executable is missing:

- the probe reports:
  - `runtime_available: false`
  - `blocker.code: "mvsim_executable_not_found"`
- the harness validation returns:
  - `status: "blocked_live_runtime_unavailable"`
  - `mvsim_mode: "blocked_live_runtime"`

This is intentional.

## What Still Remains After This Round

- a real installed `mvsim` runtime on the PC
- validated knowledge of which live pose output surface is best to bridge into sim-ingress on this machine
- one true live-runtime end-to-end tour validation after the executable exists

This round intentionally stops before ROS formalization, simulator redesign, or map-format work.
