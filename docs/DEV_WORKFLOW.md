# DEV_WORKFLOW.md

## Development Philosophy

This project uses a **vibe coding** workflow, but it must stay controlled and engineering-friendly.

The goal is not to let an agent rewrite the whole repository.  
The goal is to let an agent make fast, scoped, verifiable progress.

---

## Top-Level Workflow

### Step 1: Document first
Before meaningful feature work:
- define project goals
- define architecture boundaries
- define deployment targets
- define coding workflow

### Step 2: Mock-first implementation
Before simulation or hardware:
- create stable interfaces
- build mock adapters
- validate the application loop on a laptop

### Step 3: Simulation validation
After the mock loop works:
- connect simulated pose and state sources
- validate POI-triggered behavior in Isaac Sim

### Step 4: Embedded compatibility pass
Before real field use:
- reduce dependency weight
- verify startup strategy
- validate configs and runtime assumptions for Orin NX

### Step 5: Real hardware integration
Only after app behavior is stable:
- replace mock/sim adapters with real integrations
- debug platform issues without redesigning the product logic

---

## Bundle-Based Coding Rule

One coding round = one bundle.

A bundle should:
- have one clear purpose
- affect a limited set of files/modules
- be runnable or testable
- update docs if architecture changes

Examples:
- add AGENT/PROJECT/ARCHITECTURE docs
- add mock pose provider
- add POI manager
- add tour orchestrator state machine
- add local LLM gateway
- add Android-friendly control API

Avoid bundles like:
- “build all features”
- “clean up the whole repo”
- “refactor navigation, UI, LLM, and simulation at once”

---

## Recommended Iteration Format

For each iteration, the coding agent should:

1. Read relevant existing files
2. Explain intended changes briefly
3. Implement only the scoped bundle
4. Provide run steps
5. Provide test/validation steps
6. Report changed files
7. Commit/push if requested

---

## Mandatory Guardrails for Agents

### Do not
- broadly refactor original odin-nav-stack without explicit instruction
- introduce hidden assumptions tied to x86 only
- make desktop-specific UI choices that block Android usability
- mix simulation-specific logic into core logic
- add heavy dependencies casually without considering Orin NX

### Do
- preserve module boundaries
- prefer configuration over hardcoded behavior
- keep core logic testable without hardware
- document new interfaces and configs
- think about memory/CPU/GPU footprint early

---

## Repository Hygiene

Recommended practices:
- keep `main` usable
- work in `feature/*` branches
- use small commits
- write docs as the project evolves
- avoid long-lived undocumented drift

Suggested branches:
- `feature/docs-foundation`
- `feature/mock-pose-provider`
- `feature/poi-manager`
- `feature/local-llm-gateway`
- `feature/android-control-api`

---

## Testing Ladder

### Level 1: Static validation
- lint
- type checks if available
- config/schema validation

### Level 2: Unit validation
- POI logic
- state transitions
- content loading
- session logging

### Level 3: Mock integration
- simulated pose entering POI radius
- narration triggered correctly
- no duplicate trigger spam

### Level 4: Simulation integration
- Isaac Sim pose source
- end-to-end route validation
- session consistency

### Level 5: Embedded smoke test
- service startup on edge target
- config load
- basic control API reachable
- reduced-mode run

### Level 6: Real hardware test
- only after previous levels are stable

---

## Android-Friendly UI Workflow

The UI should be developed with Android field usage in mind.

That means:
- responsive layout early
- touch-first controls
- simple status visibility
- minimal reliance on keyboard-heavy flows
- fast access to debugging controls during robot tests

Suggested order:
1. backend API first
2. browser-friendly web UI
3. Android browser or wrapper validation
4. optional native/mobile packaging later if needed

---

## Cross-Platform Development Sequence

Recommended sequence for each major feature:
1. implement in core with mock adapter
2. verify on desktop
3. connect simulator adapter
4. verify in simulation
5. check embedded impact
6. deploy to edge target
7. connect real hardware

This sequence should be repeated consistently.

---

## Current Windows Bootstrap

For the current repo-owned Windows dev/test path, install the explicit dependency manifest first:

```shell
python -m pip install -r requirements-dev.txt
```

Then run the narrow validation ladder that is currently most useful on this machine:

```shell
python -m unittest tests.test_mvsim_validation_reporting -v
python -m unittest tests.test_mvsim_validation_map_view -v
python -m unittest tests.test_mvsim_validation_harness -v
python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml
```

Current machine truth matters here:

- if `tests.test_mvsim_validation_harness` fails because `httpx` is missing, the manifest is incomplete and should be updated
- if `scripts/print_mvsim_live_probe.py` reports `blocked_live_runtime`, the WSL/MVSim path still needs bring-up
- if `scripts/print_mvsim_live_probe.py` reports `live_runtime`, the configured `Ubuntu` distro and `/root/round033-mvsim-build/bin/mvsim` path are reachable from the current repo configuration
- do not treat that blocker as a product bug

---

## WSL / MVSim Bring-Up

When Windows WSL is not installed, the repo-local live-runtime path cannot be claimed as ready.

If WSL is already installed, skip the elevated Windows step and continue with the Ubuntu-side runtime sequence until `python scripts/print_mvsim_live_probe.py --config configs/sim_harness.yaml` reports `effective_mode = "live_runtime"`.

The elevated Windows step is:

```shell
wsl.exe --install -d Ubuntu
```

After the Ubuntu shell first-launch completes, follow the Linux-side runtime sequence described in [`docs/MVSIM_LIVE_RUNTIME_BRINGUP.md`](MVSIM_LIVE_RUNTIME_BRINGUP.md).

That Linux-side path is part of the repo-owned bootstrap story and should stay visible from this workflow doc.

---

## Codex / Agent Prompting Guidance

Prompts should be:
- scoped
- concrete
- architecture-aware
- validation-aware

Good prompt traits:
- explicitly say what not to touch
- ask for changed files and run steps
- ask for tests or smoke verification
- ask for commit/push output when needed

Bad prompt traits:
- vague large goals
- no scope constraints
- no validation requirement
- no platform/deployment awareness

---

## Cross-Thread Coordination Protocol

When work is coordinated across separate chat threads, use repository files as the handoff contract.

Recommended files:
- `coordination/latest_prompt.md`
- `coordination/latest_result.md`
- `coordination/archive/`

Recommended rule:
1. owner thread writes the latest prompt
2. execution thread reads it before work
3. execution thread writes the latest result after work
4. owner thread reviews repo state plus the latest result and decides the next round

This avoids hidden chat-thread context becoming part of the engineering process.

---

## Definition of Done for a Bundle

A bundle is done when:
- code/doc changes are complete
- the current environment can run or validate the feature
- docs are updated if needed
- limitations are clearly stated
- the repository state is understandable by the next iteration
