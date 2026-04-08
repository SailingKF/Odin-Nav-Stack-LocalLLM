# Current Round Result

## Round
Round 046 - Ubuntu WSL Provisioning And MVSim Runtime Path Verification

## Goal
Finish the missing Ubuntu distribution/runtime verification step on this PC and determine whether the configured Linux-side MVSim runtime path from the repo can actually be reached.

## Summary

- Status: `ubuntu_wsl_and_mvsim_path_verified`
- The configured distro name `Ubuntu` exists on this PC and matches the repo config.
- The configured runtime path `/root/round033-mvsim-build/bin/mvsim` was initially missing inside that distro.
- I re-ran the already documented Round 033 Ubuntu-side MVSim build path, restored the expected runtime path, and re-verified the repo probe.
- The current repo probe now reports `effective_mode = "live_runtime"` with no runtime blocker.

## What I Did

- Verified Windows-side WSL state with:
  - `wsl.exe --status`
  - `wsl.exe --list --verbose`
- Verified distro identity and shell access with:
  - `wsl.exe -d Ubuntu -u root -- bash -lc "whoami; pwd; (lsb_release -ds || . /etc/os-release && echo $PRETTY_NAME) 2>/dev/null"`
- Confirmed the configured Round 033 runtime path was missing before rebuild:
  - `/root/round033-mvsim-src`
  - `/root/round033-mvsim-build`
  - `/root/round033-mvsim-build/bin/mvsim`
- Re-ran the documented Ubuntu-side MVSim bring-up sequence inside `Ubuntu`:
  - `apt-get update`
  - `apt-get install -y software-properties-common`
  - `add-apt-repository -y ppa:joseluisblancoc/mrpt-stable`
  - `apt-get install -y libmrpt-dev mrpt-apps build-essential g++ cmake libbox2d-dev protobuf-compiler libprotobuf-dev libzmq3-dev git pybind11-dev libpython3-dev python3.12-venv`
  - `git clone --recursive https://github.com/MRPT/mvsim.git /root/round033-mvsim-src`
  - `mkdir -p /root/round033-mvsim-build`
  - `cd /root/round033-mvsim-build`
  - `cmake /root/round033-mvsim-src`
  - `cmake --build . -j2`
- Re-verified the runtime with:
  - `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml`
  - `wsl.exe -d Ubuntu -u root -- bash -lc "/root/round033-mvsim-build/bin/mvsim --help | head -n 20"`
  - `wsl.exe -d Ubuntu -u root -- bash -lc "ls -l /root/round033-mvsim-build/bin/mvsim"`
- Updated repo docs so the current machine truth is no longer stale:
  - `docs/DEV_WORKFLOW.md`
  - `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- Updated this handoff file:
  - `coordination/latest_result.md`

## Exact Files Changed

- `docs/DEV_WORKFLOW.md`
- `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
- `coordination/latest_result.md`

## What Changed In Each File

- `docs/DEV_WORKFLOW.md`
  - added the positive ready-state interpretation for `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml`
  - clarified that when WSL is already installed, the operator should continue the Ubuntu-side runtime sequence until the probe returns `effective_mode = "live_runtime"`
- `docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`
  - replaced the stale "WSL is not installed on this PC" current-machine-truth section with the verified Round 046 state
- `coordination/latest_result.md`
  - replaced the previous round result with the truthful Round 046 result and evidence

## Exact Output Summary

### `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml`

- Initial pre-build check:
  - `configured_mode = "live_runtime"`
  - `effective_mode = "blocked_live_runtime"`
  - `wsl_enablement.wsl_installed = true`
  - `live_runtime.wsl_distribution = "Ubuntu"`
  - blocker code `wsl_mvsim_executable_not_found`
  - blocker detail: configured WSL MVSim executable `/root/round033-mvsim-build/bin/mvsim` was not executable inside distribution `Ubuntu`
- Current post-build check:
  - `configured_mode = "live_runtime"`
  - `effective_mode = "live_runtime"`
  - `live_runtime.runtime_available = true`
  - `live_runtime.wsl_distribution = "Ubuntu"`
  - `live_runtime.wsl_executable_path = "/root/round033-mvsim-build/bin/mvsim"`
  - `live_runtime.world_file_exists = true`
  - `live_runtime.blocker = null`
  - `live_runtime.runtime_check.returncode = 0`
  - `live_runtime.runtime_check.stderr` still reports the localhost-proxy / NAT warning from WSL startup

### `wsl.exe --status`

- Returned success.
- Decoded stdout summary:
  - `默认分发: Ubuntu`
  - `默认版本: 2`
  - `当前计算机配置不支持 WSL1。`
  - `若要使用 WSL1，请启用“Windows Subsystem for Linux”可选组件。`

### Distro Listing / Verification Commands Used

- `wsl.exe --list --verbose`
  - showed `* Ubuntu    Stopped    2`
- `wsl.exe -d Ubuntu -u root -- bash -lc "whoami; pwd; (lsb_release -ds || . /etc/os-release && echo $PRETTY_NAME) 2>/dev/null"`
  - returned `root`
  - returned working directory `/mnt/d/Vibe Coding Projects/Odin-Nav-Stack-LocalLLM`
  - returned `Ubuntu 24.04.4 LTS`

### Runtime Path Verification Commands Used Inside WSL

- Pre-build verification:
  - `wsl.exe -d Ubuntu -u root -- bash -lc "ls -ld /root/round033-mvsim-src /root/round033-mvsim-build /root/round033-mvsim-build/bin /root/round033-mvsim-build/bin/mvsim"`
  - reported `No such file or directory` for `/root/round033-mvsim-src`, `/root/round033-mvsim-build`, `/root/round033-mvsim-build/bin`, and `/root/round033-mvsim-build/bin/mvsim`
- Post-build verification:
  - `wsl.exe -d Ubuntu -u root -- bash -lc "/root/round033-mvsim-build/bin/mvsim --help | head -n 20"`
  - printed the `mvsim v1.3.0` help banner and available commands
  - `wsl.exe -d Ubuntu -u root -- bash -lc "ls -l /root/round033-mvsim-build/bin/mvsim"`
  - reported `-rwxr-xr-x 1 root root 313464 Apr 8 18:24 /root/round033-mvsim-build/bin/mvsim`

## Config Truth

- `wsl_distribution` updated: no, it remains `Ubuntu`
- `wsl_executable_path` updated: no, it remains `/root/round033-mvsim-build/bin/mvsim`
- `/root/round033-mvsim-build/bin/mvsim` exists inside WSL: yes
- Round ended in: `ubuntu_wsl_and_mvsim_path_verified`

## Validation

### Commands Run

```text
python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml
wsl.exe --status
wsl.exe --list --verbose
wsl.exe -d Ubuntu -u root -- bash -lc "whoami; pwd; (lsb_release -ds || . /etc/os-release && echo $PRETTY_NAME) 2>/dev/null"
wsl.exe -d Ubuntu -u root -- bash -lc "ls -ld /root /root/round033-mvsim-src /root/round033-mvsim-build /root/round033-mvsim-build/bin /root/round033-mvsim-build/bin/mvsim"
wsl.exe -d Ubuntu -u root -- bash -lc "apt-get update"
wsl.exe -d Ubuntu -u root -- bash -lc "DEBIAN_FRONTEND=noninteractive apt-get install -y software-properties-common && add-apt-repository -y ppa:joseluisblancoc/mrpt-stable"
wsl.exe -d Ubuntu -u root -- bash -lc "DEBIAN_FRONTEND=noninteractive apt-get install -y libmrpt-dev mrpt-apps build-essential g++ cmake libbox2d-dev protobuf-compiler libprotobuf-dev libzmq3-dev git pybind11-dev libpython3-dev python3.12-venv"
wsl.exe -d Ubuntu -u root -- bash -lc "git clone --recursive https://github.com/MRPT/mvsim.git /root/round033-mvsim-src"
wsl.exe -d Ubuntu -u root -- bash -lc "mkdir -p /root/round033-mvsim-build && cd /root/round033-mvsim-build && cmake /root/round033-mvsim-src"
wsl.exe -d Ubuntu -u root -- bash -lc "cd /root/round033-mvsim-build && cmake --build . -j2"
python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml
wsl.exe -d Ubuntu -u root -- bash -lc "/root/round033-mvsim-build/bin/mvsim --help | head -n 20"
wsl.exe -d Ubuntu -u root -- bash -lc "ls -l /root/round033-mvsim-build/bin/mvsim"
```

### Results

- All WSL verification commands completed successfully enough to determine the real distro/runtime state.
- Ubuntu distro verification passed and matched the configured name `Ubuntu`.
- The initial runtime-path check failed because the expected Round 033 build output did not exist yet.
- The documented Ubuntu-side dependency install, clone, configure, and build sequence completed successfully in this session.
- The rebuilt runtime now satisfies the configured repo contract:
  - distro: `Ubuntu`
  - user: `root`
  - executable path: `/root/round033-mvsim-build/bin/mvsim`
- The final repo probe passed with `effective_mode = "live_runtime"`.

## Git Status

- Branch: `main`
- Current `git status --short --branch`:

```text
## main...origin/main
 M coordination/latest_prompt.md
 M coordination/latest_result.md
 M docs/DEV_WORKFLOW.md
 M docs/MVSIM_LIVE_RUNTIME_BRINGUP.md
?? coordination/archive/round-044-prompt.md
?? coordination/archive/round-044-result.md
?? coordination/archive/round-045-prompt.md
?? coordination/archive/round-045-result.md
?? requirements-dev.txt
```

- Current HEAD commit: `5f6126e5f0f86515b9e225132bd956d3583425ab`
- Files staged: no
- Files committed in this round: no
- Files pushed in this round: no

## Acceptance Criteria Check

- the current WSL distribution state is checked and recorded truthfully: yes
- the round determines whether the expected distro name `Ubuntu` exists on this PC: yes
- the round determines whether the configured MVSim path `/root/round033-mvsim-build/bin/mvsim` exists inside that distro: yes
- if either the distro or executable is missing, the exact narrow blocker and next commands are recorded: yes
- any needed config/doc changes are limited to making the repo truthful and reproducible: yes

## Risks / Blockers / Limitations

- WSL still emits a localhost-proxy / NAT warning on command startup. It did not block runtime verification or `mvsim --help`, but it may still matter for future network-dependent steps inside WSL.
- This round verified distro reachability and the configured runtime path only. It did not re-run the full live bridge or the full validation harness end-to-end route flow.
- The worktree already contained owner-side modified / untracked coordination and doc files before this round. They remain uncommitted.

## Coordination Update

- Outcome: `ubuntu_wsl_and_mvsim_path_verified`
- Distro name actually installed: `Ubuntu`
- Configured distro name kept: `Ubuntu`
- Configured executable path kept: `/root/round033-mvsim-build/bin/mvsim`
- No config fields were changed in this round.
- Next narrow step: run the live bridge or validation harness against the now-verified WSL runtime path and confirm the end-to-end live pose flow still works on this PC.
