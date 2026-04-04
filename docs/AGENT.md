# AGENT.md

## Purpose
This repository extends Odin-Nav-Stack into a **location-triggered local tour guide system** that can run first on a developer laptop, then in simulation, and later on embedded edge platforms such as **Jetson Orin NX**.

The system should support:
- map/POI-triggered narration
- local LLM-assisted tour explanation and Q&A
- Android-based deployment/debug control UI
- session logging
- video recording for **offline** analysis
- cross-platform deployment across dev workstation, simulator, and embedded edge device

---

## Non-Negotiable Engineering Principles

1. **Laptop first, simulation second, real robot last**
   - All major product logic must run without the Odin robot body.
   - The first runnable version must work on a normal development computer using mock adapters.
   - Isaac Sim is used after the mock pipeline is stable.
   - Real robot integration comes last.

2. **Embedded compatibility is a first-class requirement**
   - All new code must consider future deployment on **Jetson Orin NX** or similar embedded platforms.
   - Avoid unnecessary heavyweight dependencies.
   - Prefer modular services and interface-based design.
   - Avoid locking business logic to x86-only assumptions.

3. **Platform-specific code must stay in adapters**
   - Core application logic must not directly depend on ROS topics, Jetson paths, Android-specific behavior, or simulation-only APIs.
   - Put platform coupling into dedicated adapters.

4. **LLM is not the source of truth**
   - Tour knowledge comes from a curated content library.
   - The local LLM is used to rephrase, personalize, and answer questions using structured content.
   - The LLM must not be treated as the authoritative knowledge base.

5. **Video analysis is offline**
   - Real-time video analysis is out of scope for the initial product loop.
   - Runtime only records video and aligns it with session logs and timestamps.
   - All face/expression/action analysis happens later offline.

6. **One bundle per iteration**
   - Each coding round should make one coherent improvement.
   - Avoid broad refactors unless the task explicitly asks for one.

---

## Target Product Scope

### In Scope
- POI-triggered narration based on map position
- Android control/debug UI
- local LLM gateway
- content library
- session logs and playback metadata
- offline analytics pipeline hooks
- desktop + simulation + embedded deployment planning

### Out of Scope for Early Iterations
- full autonomous productization on real hardware
- real-time video understanding loop
- cloud dependency as a requirement
- large-scale multi-robot orchestration
- broad refactor of original odin-nav-stack before a minimal tour pipeline works

---

## Architecture Rules

### Core Layer
Must remain platform-independent whenever possible:
- POI manager
- tour orchestrator
- content service
- session logger
- narration policy
- interface definitions

### Adapter Layer
Must isolate platform/runtime integrations:
- mock pose provider
- Isaac Sim pose provider
- ROS pose provider
- Odin robot integration
- Android control bridge
- video recorder implementation
- audio IO implementation

### Service Layer
Can be separate processes:
- local LLM gateway
- TTS/ASR service
- offline analytics worker
- API backend for UI

---

## Performance and Embedded Constraints

When adding code, assume eventual deployment on Orin NX:
- avoid massive Python-only monoliths where a lean service boundary helps
- prefer configurable model backends
- avoid large always-on background workers unless necessary
- make video recording optional/configurable
- support reduced modes for edge deployment
- support CPU-only fallback for dev/testing where possible

---

## Android UI Direction

The deployment/control UI is expected to be usable on **Android** for field debugging and task control.

Design implications:
- the main control UI should be accessible through a browser-friendly web interface or Android-friendly frontend
- the backend API should be platform-agnostic
- do not hardcode desktop-only UI assumptions
- prioritize touch-friendly flows for:
  - route selection
  - POI status
  - narration start/pause/resume
  - logs/status visibility
  - quick debugging controls

---

## Required Working Style for Coding Agents

For every task:
1. read relevant existing files first
2. state what will be changed
3. keep changes scoped
4. update docs when architecture or workflow changes
5. provide run steps
6. provide validation steps
7. commit and push only after validation if requested

---

## Commit and Branch Guidance

Recommended branch strategy:
- `main`: always demoable or close to demoable
- `feature/<bundle-name>`: one bundle per branch
- merge only after smoke verification

Commit style examples:
- `docs: add cross-platform development workflow`
- `feat: add poi-triggered tour orchestrator scaffold`
- `feat: add android-friendly control api`
- `chore: add dev sim edge configs`

---

## Output Expectations for Each Coding Round

If a coding agent modifies code, it should report:
- changed files
- how to run
- how to test
- limitations
- next logical step
- git status / commit hash / push result if requested
