# DEPLOYMENT.md

## Deployment Philosophy

This project must support three practical deployment modes:

1. **Development mode** on a laptop/workstation
2. **Simulation mode** using Isaac Sim
3. **Edge mode** on embedded hardware such as **Jetson Orin NX**

The architecture should avoid requiring a redesign when moving between these modes.

In addition, the operator-facing control/debug UI should be usable from **Android**.

---

## Supported Deployment Modes

### 1. Development Mode
Purpose:
- fastest local iteration
- mock testing
- UI/backend integration
- LLM/service experimentation

Typical environment:
- x86 laptop or workstation
- optional local GPU
- browser-based UI
- mock pose provider

Recommended running components:
- core application modules
- UI backend
- UI frontend
- local or configurable LLM gateway
- mock adapters
- local logging/session store

### 2. Simulation Mode
Purpose:
- validate runtime behavior without the real robot
- verify position-triggered narration in a controlled environment
- test route/POI behavior end-to-end

Typical environment:
- x86 workstation with suitable GPU
- Isaac Sim
- simulator pose adapter
- browser/Android-accessible UI

Recommended running components:
- same app services as development mode
- Isaac Sim adapter instead of mock pose
- optional simulated audio/video hooks

### 3. Edge Mode
Primary target:
- **Jetson Orin NX**

Purpose:
- field deployment
- local control
- local narration / local inference
- resource-aware runtime

Expected characteristics:
- tighter compute budget
- tighter memory budget
- more fragile device dependencies
- stronger need for startup reliability

Recommended running components:
- only essential services always-on
- optional reduced-mode inference
- optional disablement of non-critical analytics
- hardware adapters for pose/audio/video
- local backend API for Android control client

---

## Android UI Deployment Direction

The control/debug UI should be designed so that Android can be used as a practical field control terminal.

Preferred strategy:
- provide a **web-based responsive UI** first
- access it through Android browser or web wrapper
- keep backend APIs clean and platform-agnostic

Advantages:
- faster than building a full native Android app early
- easier to debug
- easier to reuse on desktop and tablet
- good fit for field troubleshooting

Android usage scenarios:
- start/pause/resume tour
- inspect current POI
- inspect current state machine state
- check logs or errors
- switch route/profile
- confirm health/readiness

---

## Packaging Strategy

### Early Stage
Do not over-containerize.

Recommended:
- run hardware-coupled pieces on host
- run optional backend services separately
- keep startup scripts simple
- focus on reliability and visibility

### Later Stage
Introduce containers where they help:
- backend API
- LLM gateway
- offline analytics worker
- UI frontend/backend packaging

Be cautious with:
- audio device access
- video device access
- ROS/hardware access
- GPU pass-through on embedded devices

---

## Configuration Strategy

Use explicit environment configs.

Suggested files:
- `configs/dev.yaml`
- `configs/sim.yaml`
- `configs/edge.yaml`
- `services/deployment_profile/profile.py`

These should control:
- pose provider implementation
- UI host/port
- LLM backend selection
- logging level
- recording enable/disable
- edge resource mode
- audio configuration
- video configuration

Do not fork behavior through scattered hardcoded checks.

Current runtime-facing profile summary now exposes:
- deployment class
- readiness status
- expected pose/audio/LLM characteristics
- active mock-only components
- placeholder components that still block true edge readiness
- validation warnings/errors for obvious mismatches
- preflight dependency checks and safe local probes

See also:
- `docs/DEPLOYMENT_PROFILE_CONTRACT.md`
- `docs/DEPLOYMENT_PREFLIGHT_CONTRACT.md`

---

## Orin NX Compatibility Guidelines

All feature work should assume eventual deployment on Orin NX.

### Design Guidelines
- prefer lean dependencies
- avoid unnecessary background services
- allow optional subsystem disablement
- support lower-memory modes
- minimize idle resource consumption
- keep API boundaries stable so services can be colocated or split

### Practical Concerns
- model size selection matters
- TTS/ASR backend choice matters
- video recording settings must be configurable
- build/startup process must be reproducible
- debugging without a full desktop environment should remain possible

### Recommendation
Treat Orin NX as a constrained but first-class target, not an afterthought.

---

## Suggested Runtime Topologies

### Topology A: Dev Laptop
- UI frontend
- UI backend
- core app
- mock pose provider
- local LLM gateway
- local session storage

### Topology B: Sim Workstation
- Isaac Sim
- UI backend
- core app
- simulator pose adapter
- optional local LLM gateway
- local or network session storage

### Topology C: Edge Device + Android Client
On Orin NX:
- core app
- backend API
- pose/audio/video adapters
- optional local LLM/TTS stack

On Android:
- browser/web app control UI

This split is recommended for field simplicity.

---

## Deployment Sequence Recommendation

### Stage 1
Laptop-only runnable demo

### Stage 2
Laptop + simulator validation

### Stage 3
Edge packaging dry run without full hardware dependence

### Stage 4
Edge with partial device integrations

### Stage 5
Full field deployment

Do not skip directly from docs to real hardware deployment.

---

## Startup and Service Control

Eventually, each environment should have a clear startup method:
- dev scripts for development
- sim scripts for simulation
- edge startup scripts or system services for deployment

Suggested future directions:
- `scripts/run_dev.sh`
- `scripts/run_sim.sh`
- `scripts/run_edge.sh`

For edge:
- consider systemd-managed services when the application stabilizes

---

## Validation Checklist by Environment

### Dev
- app boots
- mock pose triggers POIs
- UI reachable
- session logs written
- deployment profile reports `deployment_class: dev_only`
- deployment profile reports `readiness_status: ready_for_profile`

### Sim
- sim pose reaches app
- route/POI trigger works
- logs remain coherent
- Android-accessible UI works over network
- deployment profile reports `deployment_class: sim_only`
- deployment profile reports live vs stub simulator status clearly

### Edge
- services boot reliably
- config loads correctly
- UI reachable from Android
- reduced resource mode works
- core tour loop works even if non-essential services are disabled
- deployment profile reports whether the current config is still placeholder/mock
- obvious pose/audio/LLM mismatches appear as validation warnings or errors
- preflight reports which dependencies are:
  - locally probeable now
  - unreachable
  - missing
  - still external/unverified

---

## Deployment Rule of Thumb

If a new feature makes desktop development easier but makes embedded deployment brittle, redesign it early.

The system must remain:
- mockable
- sim-compatible
- edge-aware
- Android-operable
