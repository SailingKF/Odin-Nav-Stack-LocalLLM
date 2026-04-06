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

Current live-validation alignment note:

- for the Round 035 baseline, the world init pose is intentionally aligned to the first current POI
- this keeps the change narrow while proving the first live-triggered narration event
- the chosen alignment is recorded in `configs/sim.yaml` under:
  - `mvsim_integration.live_validation_alignment`

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

## Current Truth After Round 033

On this PC, a real Linux-side MVSim runtime now exists inside Ubuntu on WSL2.

What is true now:

- WSL2 is installed and Ubuntu 24.04 launches successfully
- MRPT dev packages can be installed from the official MRPT stable PPA
- `mvsim` can be built from source inside Ubuntu
- the repo-local minimal world can be launched from that Linux runtime in `--headless` mode

What is **not** true yet:

- there is still no Windows-native `mvsim.exe`
- the validated live runtime currently lives in WSL, not on the Windows PATH
- only a minimal live pose bridge baseline exists so far; full live route progression is not implemented yet

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

## Round 032 WSL Enablement Findings

The next round tested the WSL path directly on this PC.

### What was confirmed

- `wsl.exe` exists on this PC
- WSL itself is **not** installed yet
- the current shell is **not** elevated

Observed from repo-local probe output:

- `wsl_command_available: true`
- `wsl_installed: false`
- `current_shell_elevated: false`
- `blocker.code: "wsl_requires_elevation"`

### What this means

The narrowest real blocker has become:

- WSL enablement requires an elevated Windows shell on this PC

So this round does not broaden into Linux package installation or MVSim build steps inside WSL, because the base WSL feature cannot be enabled from the current session.

### Recommended next command

From an elevated Windows terminal:

```text
wsl.exe --install -d Ubuntu
```

After reboot / first-launch completion, the next narrow step would be:

- verify `wsl.exe --status`
- verify Ubuntu starts
- install the Linux-side MVSim/MRPT runtime there

## Round 033 Linux-Side Runtime Enablement

This round moved past WSL enablement and into a truthful Ubuntu-side runtime bring-up.

### Exact Linux-side commands that succeeded

Inside Ubuntu 24.04 on WSL2, the narrow successful path was:

```text
apt-get update
apt-get install -y software-properties-common
add-apt-repository -y ppa:joseluisblancoc/mrpt-stable
apt-get install -y libmrpt-dev mrpt-apps
apt-get install -y build-essential g++ cmake libbox2d-dev protobuf-compiler libprotobuf-dev libzmq3-dev git
apt-get install -y pybind11-dev libpython3-dev python3.12-venv
git clone --recursive https://github.com/MRPT/mvsim.git /root/round033-mvsim-src
mkdir -p /root/round033-mvsim-build
cd /root/round033-mvsim-build
cmake /root/round033-mvsim-src
cmake --build . -j2
```

### Verified Linux-side runtime command

The verified executable is:

```text
/root/round033-mvsim-build/bin/mvsim
```

Verification:

```text
/root/round033-mvsim-build/bin/mvsim --help
```

### Repo-local world launch result

The first truthful world launch attempt used:

```text
/root/round033-mvsim-build/bin/mvsim launch /mnt/c/Users/saili/Desktop/odin_nav_stack_local_llm_docs/content/sim/mvsim/worlds/odin_minimal_tour.world.xml --headless -v INFO
```

Observed progression:

1. the original repo world failed on color parsing because current MVSim expects `#RRGGBB[AA]`
2. after updating the world colors, launch failed again because current MVSim expects `<walls><shape>...</shape></walls>` or a model URI instead of legacy repeated `<wall>` tags
3. after updating the repo-local world to the current wall schema, the headless launch stayed alive and had to be terminated manually by the validation probe

So the world asset is now aligned with the current Linux-side MVSim parser contract used in this repo.

### Operator note

`configs/sim.yaml` now records the validated WSL-side runtime path explicitly:

- `mvsim_integration.runtime_host: wsl`
- `mvsim_integration.wsl_distribution: Ubuntu`
- `mvsim_integration.wsl_user: root`
- `mvsim_integration.wsl_executable_path: /root/round033-mvsim-build/bin/mvsim`

This does not switch the validated end-to-end sim flow away from the compatibility shim.
It only records the truthful location of the live MVSim runtime for the next bridge step.

## Round 034 Live Pose Surface Discovery

The next narrow integration seam was validated against the real WSL runtime.

Discovered live pose surface:

- topic:
  - `/tour_bot/pose`
- type:
  - `mvsim_msgs.TimeStampedPose`
- observed publisher:
  - `World`
- observed rate:
  - about `9.6 Hz`

The current minimal bridge uses:

- `wsl.exe ... mvsim topic echo /tour_bot/pose`

and parses:

- `objectId`
- `pose.x`
- `pose.y`
- `pose.yaw`

into the existing Windows-side `sim_pose_ingress` shape.

Focused bridge doc:

- `docs/MVSIM_LIVE_POSE_BRIDGE.md`

## Round 035 Live Route Alignment And First Narration Trigger

The next narrow step was to close the first product-level event boundary instead of stopping at `last_pose` updates.

Chosen alignment strategy:

- keep the current `demo_pois.yaml` content unchanged
- keep the current live bridge path unchanged
- move only the repo-local MVSim world init pose to the first current POI:
  - `East Gate` at `(0.0, 0.0)`

What this enables truthfully:

- the first live `/tour_bot/pose` sample lands inside the first POI trigger radius
- `sim_pose_ingress` records a real `poi_triggered`
- the existing orchestrator records a real `narration_started`
- `/debug` can observe the resulting narration through the sim-profile API proxy

This remains a narrow validation asset choice, not a claim of full live autonomous progression.

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

- moving beyond the first live POI hit into truthful continuous live route progression
- deciding whether the minimal MVSim world should gain controlled motion or stay a first-hit-only validation asset
- validating a second live POI hit only if that can be done without simulator redesign

This round intentionally stops before ROS formalization, simulator redesign, or map-format work.
