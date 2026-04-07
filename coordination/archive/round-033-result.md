# Current Round Result

## Round
Round 033 - WSL MVSim Runtime Install And First Linux-Side World Launch

## Summary

- Status: `linux_runtime_enabled`
- This round moved past WSL enablement and completed a truthful Linux-side MVSim bring-up in Ubuntu 24.04 on WSL2.
- A real Linux-side `mvsim` executable now exists on this PC:
  - `/root/round033-mvsim-build/bin/mvsim`
- The repo-local minimal world was used in a real Linux-side launch attempt.
- The world initially hit two real parser-level blockers against the current MVSim version:
  - color fields had to move from float triples to `#RRGGBB`
  - legacy repeated `<wall>` tags had to move to `<walls><shape><pt>...</pt></shape></walls>`
- After those minimal repo-local asset fixes, the headless world launch stayed alive in WSL until terminated by the probe harness.

## What I Changed

- Made the live-runtime probe WSL-aware so the repo can truthfully report a Linux-side MVSim runtime instead of only looking for a Windows PATH executable:
  - `services/sim_publisher_bridge/mvsim_live.py`
- Added focused tests for the new WSL runtime-host path:
  - `tests/test_mvsim_live_runtime.py`
- Updated the sim config to record the validated WSL runtime location:
  - `configs/sim.yaml`
- Updated the repo-local minimal world to match the current MVSim parser contract:
  - `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`
- Updated focused docs and operator guidance:
  - `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`
  - `README.md`

## Exact Files Changed

- `README.md`
- `configs/sim.yaml`
- `content/sim/mvsim/worlds/odin_minimal_tour.world.xml`
- `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `services/sim_publisher_bridge/mvsim_live.py`
- `tests/test_mvsim_live_runtime.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Whether `mvsim` Became Runnable Inside Ubuntu/WSL

Yes.

The truthful verified Linux-side executable is:

```text
/root/round033-mvsim-build/bin/mvsim
```

And it now probes successfully from the repo via:

```text
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
```

which currently reports:

- `runtime_host: "wsl"`
- `runtime_available: true`
- `blocker: null`

## Exact Commands Used For Package Install / Build / Runtime Verification

### WSL and Ubuntu verification

```text
wsl.exe --status
wsl.exe -l -v
wsl.exe -d Ubuntu -- bash -lc "uname -a; lsb_release -a 2>/dev/null || cat /etc/os-release; whoami; pwd"
```

### Ubuntu package and repo enablement

```text
wsl.exe -d Ubuntu -u root -- bash -lc "apt-get update"
wsl.exe -d Ubuntu -u root -- bash -lc "apt-get install -y software-properties-common"
wsl.exe -d Ubuntu -u root -- bash -lc "add-apt-repository -y ppa:joseluisblancoc/mrpt-stable"
wsl.exe -d Ubuntu -u root -- bash -lc "apt-get install -y libmrpt-dev mrpt-apps"
wsl.exe -d Ubuntu -u root -- bash -lc "apt-get install -y build-essential g++ cmake libbox2d-dev protobuf-compiler libprotobuf-dev libzmq3-dev git"
wsl.exe -d Ubuntu -u root -- bash -lc "apt-get install -y pybind11-dev libpython3-dev python3.12-venv"
```

### Source clone and build

```text
wsl.exe -d Ubuntu -u root -- bash -lc "git clone --recursive https://github.com/MRPT/mvsim.git /root/round033-mvsim-src"
wsl.exe -d Ubuntu -u root -- bash -lc "mkdir -p /root/round033-mvsim-build && cd /root/round033-mvsim-build && cmake /root/round033-mvsim-src"
wsl.exe -d Ubuntu -u root -- bash -lc "cd /root/round033-mvsim-build && cmake --build . -j2"
```

### Runtime verification

```text
wsl.exe -d Ubuntu -u root -- bash -lc "cd /root/round033-mvsim-build && ./bin/mvsim --help"
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
```

### Repo-local world launch attempts

Initial truthful launch command:

```text
wsl.exe -d Ubuntu -u root -- bash -lc "cd /root/round033-mvsim-build && ./bin/mvsim launch /mnt/c/Users/saili/Desktop/odin_nav_stack_local_llm_docs/content/sim/mvsim/worlds/odin_minimal_tour.world.xml --headless -v INFO"
```

The same command was re-run after each minimal world-asset fix.

## What Linux-side Executable / Command Now Works

Verified command:

```text
/root/round033-mvsim-build/bin/mvsim --help
```

Verified launch form:

```text
/root/round033-mvsim-build/bin/mvsim launch /mnt/c/Users/saili/Desktop/odin_nav_stack_local_llm_docs/content/sim/mvsim/worlds/odin_minimal_tour.world.xml --headless -v INFO
```

## What Happened When Launching The Repo-Local World

### First truthful launch attempt

Observed output:

```text
Error parsing 'color'='0.92 0.92 0.92' (Expected format:'#RRGGBB[AA]')
```

Conclusion:

- the repo-local world was using an older color syntax than the current Linux-side MVSim parser accepts

### Second truthful launch attempt

After changing colors to hex, observed output:

```text
Assert condition failed: !wallModelFileName.empty()
Location: .../World_walls.cpp
```

Conclusion:

- the repo-local world was still using legacy repeated `<wall>` tags
- current MVSim expects either:
  - `<walls><shape> ... </shape></walls>`
  - or a model-backed wall definition

### Third truthful launch attempt

After converting the wall section to the current `<shape>` contract:

- the headless process stayed alive for at least 2 seconds
- a validation probe then terminated it intentionally
- no further XML/parser/runtime blocker was observed in that launch

This is the first truthful repo-local Linux-side world launch success state for this PC.

## Whether The Round Ended In `linux_runtime_enabled`, `linux_runtime_attempted_but_blocked`, Or `linux_install_blocked`

This round ended in:

- `linux_runtime_enabled`

## What The Next Narrow Step Is Before Implementing A Live Pose Bridge

The next narrow step is:

1. inspect which live pose output surface from the running Linux-side MVSim process is the smallest reliable bridge target
2. capture that output contract without broadening into ROS or simulator redesign
3. route that live output into the existing Windows-side sim-ingress / tour-validation path

This is now a live bridge question, not a base runtime-install question.

## Exact Validation Performed

### Runtime / operator validation

- `python scripts/print_mvsim_live_probe.py --config configs/sim.yaml`
  - passed
  - confirmed:
    - `runtime_host: "wsl"`
    - `runtime_available: true`
    - `world_file_exists: true`
    - `launch_command` is a `wsl.exe -d Ubuntu ...` launch form
- `wsl.exe -d Ubuntu -u root -- bash -lc "cd /root/round033-mvsim-build && ./bin/mvsim --help"`
  - passed
- real headless launch attempt of the repo-local world
  - first run exposed color-schema blocker
  - second run exposed wall-schema blocker
  - third run stayed alive successfully after repo-local fixes

### Automated

- `python -m unittest tests.test_mvsim_live_runtime -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 111 tests ... OK`

## Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 35]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `bf038cc175d509705e6e5a486e55b2acd888740a`

## Whether Files Are Staged And / Or Committed

- Round 033 repo changes: committed
- no files remain staged
- `coordination/latest_result.md`: updated locally after commit, not staged
- unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule
- temporary runtime-attempt folders remain untracked and outside this commit

## Blockers, Risks, Or Remaining Gaps

- The validated live runtime currently lives in WSL under a root-owned build path:
  - `/root/round033-mvsim-build/bin/mvsim`
- There is still no Windows-native `mvsim.exe`
- The current end-to-end validated sim path is still the compatibility shim
- A live pose bridge from the running Linux-side MVSim process into the existing Windows-side stack has not been implemented yet
- WSL still emits a benign NAT/proxy warning on startup:
  - localhost proxy settings from Windows are not mirrored into WSL
  - this did **not** block package install, source clone, build, or headless launch during this round
