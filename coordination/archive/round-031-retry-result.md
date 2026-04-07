# Current Round Result

## Round
Round 031 Retry - MVSim Runtime Enablement And First Live Bring-Up

## Summary

- Status: `install_blocked`
- This round pushed the environment blocker forward substantially.
- We now know on this Windows PC:
  - there is still no usable `mvsim` executable
  - no package-manager path was found for `mvsim` or `mrpt`
  - WSL is not installed
  - a Windows source-build attempt can start, but the enablement path is blocked by missing MRPT and then by incomplete dependency retrieval for MRPT itself

This is no longer a vague “runtime missing” state.
The blocker is now concrete and reproducible.

## What I Changed

- Updated the live-runtime bring-up doc with the retry-round environment findings:
  - `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- Updated README so the repo now states the current Windows enablement blocker explicitly:
  - `README.md`

No architecture changes were made in this round.
I intentionally kept the bundle narrow and environment-focused.

## Exact Files Changed

- `README.md`
- `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Whether `mvsim` Was Successfully Installed Or Enabled On This PC

No.

`mvsim` was **not** successfully installed or enabled on this PC in this round.

## Exact Commands Used For Install / Discovery / Bring-Up

### Runtime discovery

```text
Get-Command mvsim -ErrorAction SilentlyContinue | Format-List *
where.exe mvsim
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
```

### Environment capability checks

```text
Get-Command winget
Get-Command choco
Get-Command wsl
wsl.exe --status
winget search mvsim
winget search mrpt
choco search mvsim --exact
choco search mrpt
Get-Command git
Get-Command cmake
Get-ChildItem 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
& 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe' -all -products * -format json
Get-ChildItem 'C:\Program Files\Microsoft Visual Studio\2022' -Recurse -Filter cl.exe
```

### First source-build attempt for `mvsim`

```text
git clone --depth 1 --recursive https://github.com/MRPT/mvsim.git <tmp>\mvsim
git clone --depth 1 https://github.com/MRPT/mvsim.git <tmp>\mvsim
Invoke-WebRequest https://github.com/MRPT/mvsim/archive/refs/heads/master.zip
Expand-Archive <tmp>\mvsim-master.zip
call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
cmake -S <tmp>\mvsim-master -B <tmp>\mvsim-build -G "Visual Studio 17 2022" -A x64
```

### Dependency follow-up attempt for MRPT

```text
Invoke-RestMethod https://api.github.com/repos/MRPT/mrpt/releases/latest
Invoke-WebRequest https://github.com/MRPT/mrpt/releases/download/2.15.11/mrpt-2.15.11.zip
Expand-Archive <tmp>\mrpt-2.15.11.zip
call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64
cmake -S <tmp>\home\jlblanco\mrpt_release\mrpt-2.15.11 -B <tmp>\mrpt-build -G "Visual Studio 17 2022" -A x64
```

## What Executable Path Or Command Now Works, If Any

None.

There is still no working local command such as:

- `mvsim`
- `C:\...\mvsim.exe`

No executable path was enabled during this round.

## What Happened At Each Step

### 1. Native runtime discovery

Observed:

- `Get-Command mvsim`
  - no result
- `where.exe mvsim`
  - `INFO: Could not find files for the given pattern(s).`

Conclusion:

- no `mvsim` runtime is currently installed or discoverable on PATH

### 2. Package-manager route

Observed:

- `winget search mvsim`
  - no package found
- `winget search mrpt`
  - no package found
- `choco search mvsim --exact`
  - `0 packages found`
- `choco search mrpt`
  - `0 packages found`

Conclusion:

- no practical package-manager install route was found for this PC

### 3. WSL route

Observed:

- `wsl.exe --status`
  - reported that WSL is not installed

Conclusion:

- the most practical Linux-style installation path is not currently available on this PC

### 4. Windows toolchain route

Observed:

- available:
  - `git`
  - `cmake`
  - Visual Studio Community 2022
  - `cl.exe` under the VS install tree
- not already on PATH:
  - `cl`
  - `msbuild`
  - `ninja`

But `VsDevCmd.bat` successfully enabled the MSVC toolchain for command-line use.

Conclusion:

- Windows source-build tooling is partially available
- source-build remained worth attempting

### 5. `mvsim` source-build attempt

Observed:

- direct `git clone` attempts to GitHub failed:
  - `error: RPC failed; curl 28 Recv failure: Connection was reset`
  - `Failed to connect to github.com port 443`
- downloading the source zip via `Invoke-WebRequest` succeeded
- CMake configure for `mvsim` then failed with:
  - missing `mrpt-maps`
  - missing MRPT package config files

Conclusion:

- `mvsim` cannot be built first on this PC
- MRPT must be installed or built before `mvsim`

### 6. MRPT source-build attempt

Observed:

- GitHub release API worked
- latest MRPT release was:
  - `2.15.11`
- MRPT release zip downloaded successfully
- MRPT CMake configure started successfully under VS/MSVC
- MRPT configure then failed because required dependency content was missing from the source-tree path being used, including:
  - `3rdparty/nanogui/ext/glfw`
  - `3rdparty/nanoflann`

Conclusion:

- the release zip alone was not sufficient for a clean Windows-from-source bring-up in this attempt
- the likely next requirement is:
  - full git/submodule retrieval
  - or a better documented Windows source package path

## Whether The Round Ended In `live_runtime_enabled`, `live_runtime_attempted_but_blocked`, Or `install_blocked`

This round ended in:

- `install_blocked`

Why:

- there was no usable runtime to launch
- the environment did not advance far enough to produce a runnable `mvsim` binary
- therefore the first live-world process launch could not honestly happen yet

## What Happened When Launching The Repo-Local World

No real live world launch occurred.

What exists:

- repo-local world file:
  - `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`
- repo-local vehicle file:
  - `content/sim/mvsim/definitions/odin_tour_bot.vehicle.xml`
- computed launch shape:
  - `mvsim launch <world-file>`

What prevented launch:

- no runnable `mvsim` binary was produced or installed

## Whether The Harness Now Reports Live Runtime Available

No.

It still reports live runtime unavailable for the current `configs/sim.yaml` environment.

Observed from:

```text
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
```

and from the harness status surface:

- `live_runtime.runtime_available: false`
- `world_file_exists: true`
- compatibility source remains ready

## Exact Validation Performed

### Automated repo tests

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

### Manual validation

Confirmed:

- package-manager path not available
- WSL path not available
- VS/MSVC toolchain partially available
- `mvsim` source configure blocked on missing MRPT
- MRPT source configure blocked on incomplete dependency tree from the downloaded source package

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 33]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `c3a339f69b3462c9a124a9fdf3743fb5d6a24ab6`

## Whether Files Are Staged And / Or Committed

- Round 031 Retry repo changes: committed
- no files remain staged
- `coordination/latest_result.md`: updated locally after commit, not staged
- unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule
- temporary runtime-attempt folders remain untracked and outside this commit

## Blockers, Risks, Or Remaining Gaps Before The Next Live Pose Bridge Step

- The immediate blocker is environment enablement, not simulator architecture.
- The next realistic options are now clear:
  1. install WSL and use the Linux MVSim/MRPT route
  2. restore reliable git/submodule access on Windows and build MRPT first, then `mvsim`
- Until one of those happens, there is still no truthful way to claim:
  - live process launch
  - live pose extraction
  - live pose bridge into sim-ingress
  - live end-to-end tour completion

This round intentionally stopped at that exact blocker and did not expand scope into ROS, simulator redesign, or map-format work.
