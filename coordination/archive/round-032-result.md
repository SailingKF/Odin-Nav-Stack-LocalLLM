# Current Round Result

## Round
Round 032 - WSL Enablement For MVSim And First Linux-Side Bring-Up

## Summary

- Status: `wsl_install_blocked`
- This round proved that WSL is the right next enablement path, but it cannot be completed from the current session because:
  - `wsl.exe` exists
  - WSL itself is not installed
  - the current shell is not elevated
- The repo now surfaces that blocker directly through:
  - `python scripts/print_mvsim_live_probe.py --config configs/sim.yaml`
  - the MVSim validation harness `/status` and `/harness` page

This round did not broaden into Linux package installation or Linux-side MVSim build steps, because the base WSL feature cannot yet be enabled from this session.

## What I Changed

- Extended the live-runtime probe layer to report WSL enablement state:
  - `services/sim_publisher_bridge/mvsim_live.py`
- Added focused tests for WSL enablement evaluation:
  - `tests/test_mvsim_live_runtime.py`
- Extended the MVSim validation harness UI surface so operators can see:
  - whether WSL is installed
  - whether the current shell is elevated
  - the current WSL blocker
  - `services/mvsim_validation_harness/static/index.html`
- Updated focused docs:
  - `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
  - `docs/MVSIM_VALIDATION_HARNESS.md`
- Updated README to explain the current WSL blocker and the next narrow action:
  - `README.md`

## Exact Files Changed

- `README.md`
- `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- `docs/MVSIM_VALIDATION_HARNESS.md`
- `services/mvsim_validation_harness/static/index.html`
- `services/sim_publisher_bridge/mvsim_live.py`
- `tests/test_mvsim_live_runtime.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## Whether WSL Was Successfully Enabled On This PC

No.

WSL was **not** successfully enabled in this round.

## What Linux Distribution / Environment Was Used

None.

No Linux distribution was installed or launched in this round because the base WSL feature is not installed yet.

## Whether `mvsim` Became Runnable Inside WSL

No.

Because WSL could not be enabled from the current shell, there was no Linux environment in which `mvsim` could be installed or executed.

## Exact Commands Used For WSL Setup, Package Install / Build, And World Bring-Up

### WSL discovery and enablement checks

```text
wsl.exe --status
dism.exe /online /Get-FeatureInfo /FeatureName:Microsoft-Windows-Subsystem-Linux
dism.exe /online /Get-FeatureInfo /FeatureName:VirtualMachinePlatform
wsl.exe --list --online
wsl.exe --install -d Ubuntu
whoami /groups
```

### Repo-local runtime probes

```text
python scripts/print_mvsim_live_probe.py --config configs/sim.yaml
python -m unittest tests.test_mvsim_live_runtime -v
python -m unittest tests.test_mvsim_validation_harness -v
python -m unittest discover -s tests
```

### Operator surface verification

```text
python scripts/run_mvsim_validation_harness.py --config configs/sim.yaml --host 127.0.0.1 --port 8312
GET http://127.0.0.1:8312/status
```

## Whether The Round Ended In `wsl_runtime_enabled`, `wsl_enabled_but_mvsim_blocked`, Or `wsl_install_blocked`

This round ended in:

- `wsl_install_blocked`

## What Happened During WSL Enablement

### 1. `wsl.exe` exists

Observed:

- `Get-Command wsl`
  - returned:
    - `C:\Windows\system32\wsl.exe`

Conclusion:

- the command surface is present on Windows

### 2. WSL is not installed

Observed from both:

- `wsl.exe --status`
- `wsl.exe --list --online`

The command returned the same message:

- `The Windows Subsystem for Linux is not installed.`
- `You can install by running 'wsl.exe --install'.`

In repo-local probe output this appeared as:

- `wsl_installed: false`

### 3. The current shell is not elevated

Observed from:

- `whoami /groups`

Notable lines:

- `BUILTIN\Administrators`
  - `Group used for deny only`
- mandatory label remained:
  - `Medium Mandatory Level`

Also observed from:

- `dism.exe /online /Get-FeatureInfo ...`

which returned:

- `Error: 740`
- `Elevated permissions are required to run DISM.`

Conclusion:

- the current session is not elevated, so WSL enablement cannot proceed here

### 4. Direct install attempt did not proceed

Observed from:

- `wsl.exe --install -d Ubuntu`

The command still returned the “WSL is not installed” guidance message, but enablement did not proceed in this non-elevated session.

Combined with the DISM result, the real blocker is:

- administrator elevation is required to enable WSL on this PC

## What Happened When Launching The Repo-Local World From WSL

No WSL-side world launch occurred.

Reason:

- no WSL Linux environment was available yet

So there was no truthful attempt of:

```text
mvsim launch content/sim/mvsim/worlds/odin_minimal_tour.world.xml
```

inside Linux during this round.

## What The Next Narrow Step Is Before Implementing A Live Pose Bridge

The next narrow step is:

1. open an **elevated** Windows terminal
2. run:

```text
wsl.exe --install -d Ubuntu
```

3. reboot / complete first-launch user setup if prompted
4. verify:

```text
wsl.exe --status
```

5. only then proceed to Linux-side MVSim/MRPT installation and the first true `mvsim launch <world-file>` attempt

That is still an environment-enablement step, not a sim-stack refactor.

## Whether The Harness Now Reports Live Runtime Available

No.

What it now reports more clearly is:

- `configured_mode: "compatibility_shim"`
- `wsl_installed: false`
- `shell_elevated: false`
- `wsl_blocker: "wsl_requires_elevation"`

Observed from a real harness status call on port `8312`.

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_mvsim_live_runtime -v`
  - passed
  - `Ran 4 tests ... OK`
- `python -m unittest tests.test_mvsim_validation_harness -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 109 tests ... OK`

### Manual

Verified:

- `wsl.exe` exists
- WSL itself is not installed
- `DISM` requires elevation
- the current shell is not elevated
- the repo-local live probe now reports:
  - `wsl_command_available: true`
  - `wsl_installed: false`
  - `current_shell_elevated: false`
  - `blocker.code: "wsl_requires_elevation"`
- the harness `/status` surface now exposes the same truth

## Branch

- `main`

## Full `git status --short --branch`

```text
## main...origin/main [ahead 34]
 M docs/DEV_WORKFLOW.md
?? coordination/
?? tmp_mvsim_harness_smoke/
?? tmp_mvsim_runtime_attempt/
```

## Commit Hash

- `418433e3c29364e7bb5145986d502646c5c1c8ee`

## Whether Files Are Staged And / Or Committed

- Round 032 repo changes: committed
- no files remain staged
- `coordination/latest_result.md`: updated locally after commit, not staged
- unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule
- temporary runtime-attempt folders remain untracked and outside this commit

## Blockers, Risks, Or Remaining Gaps

- The blocker is now precise and external:
  - WSL enablement requires an elevated Windows shell on this PC
- Until that step is done, we cannot honestly claim:
  - Ubuntu installed
  - Linux-side toolchain readiness
  - Linux-side `mvsim` command available
  - Linux-side world launch attempted
- This round intentionally stopped before Linux package install/build work because doing more from a non-elevated session would not change the blocker.
