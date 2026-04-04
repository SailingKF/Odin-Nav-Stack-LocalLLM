# ARCHITECTURE.md

## System Overview

The system is a **location-triggered guided-tour application layer** built on top of Odin-Nav-Stack.

It is designed around the idea that:
- position awareness triggers narration
- curated content provides the knowledge base
- a local LLM provides natural explanation and Q&A
- control/debug interaction should be available from Android
- video is recorded during runtime and analyzed offline
- the same core logic must survive migration from desktop to simulation to embedded deployment

---

## Architectural Principles

1. **Core logic must be platform-independent**
2. **Platform bindings belong in adapters**
3. **Local-first operation is preferred**
4. **Embedded deployment constraints must be considered from day one**
5. **Android UI support should shape API design**
6. **Video analysis is offline, not in the runtime loop**

---

## High-Level Layers

### 1. Core Layer
Pure application logic.  
Should be portable across desktop, simulator, and edge.

Expected modules:
- `poi_manager`
- `tour_orchestrator`
- `content_service`
- `session_logger`
- `narration_policy`
- `interfaces`

### 2. Adapter Layer
Bridges platform/runtime specifics into the core layer.

Expected modules:
- `mock_pose_provider`
- `isaac_pose_provider`
- `ros_pose_provider`
- `odin_pose_provider`
- `video_recorder_adapter`
- `audio_io_adapter`
- `android_ui_bridge` (or mobile-friendly API adapter)
- `llm_backend_adapter`

### 3. Service Layer
Process-separated or deployable services.

Expected modules:
- `llm_gateway`
- `tts_service`
- `asr_service`
- `offline_analytics_worker`
- `ui_backend_api`

### 4. UI Layer
Touch-friendly control and debugging interface.
Primary operational target: **Android-friendly frontend**.

Expected capabilities:
- route selection
- POI state display
- current narration status
- pause/resume/skip
- health/status checks
- session list/replay entry points

---

## Data Flow

### Runtime Tour Flow
1. Pose provider emits current robot position
2. `poi_manager` determines whether a POI trigger condition is met
3. `tour_orchestrator` changes state
4. `content_service` retrieves structured tour content
5. `llm_gateway` optionally reformulates narration or answers questions
6. `tts_service` or audio layer plays speech
7. `session_logger` records the event
8. `video_recorder_adapter` aligns timestamps to the session

### Offline Analysis Flow
1. recorded session is completed
2. video and session logs are indexed
3. `offline_analytics_worker` processes selected sessions
4. analysis results are attached back to the session metadata

---

## Key Runtime State Machine

Recommended states:
- `IDLE`
- `NAVIGATING`
- `APPROACHING_POI`
- `ARRIVED_POI`
- `PLAYING_NARRATION`
- `WAITING_FOR_QUESTION`
- `ANSWERING_QUESTION`
- `CONTINUE_ROUTE`
- `PAUSED`
- `ERROR_RECOVERY`

State machine ownership:
- `tour_orchestrator`

---

## Core Interfaces

These should be defined early and kept stable.

### PoseProvider
Responsibilities:
- expose current pose
- abstract source of pose from mock / Isaac / ROS / Odin

### PoiStore
Responsibilities:
- load POI configuration
- provide POI lookup
- store trigger settings

### ContentProvider
Responsibilities:
- return curated content for a POI
- support tour modes or variants

### NarrationEngine
Responsibilities:
- generate final narration from structured content
- answer follow-up questions using curated context

### AudioOutput
Responsibilities:
- play generated speech
- support stop/pause/resume hooks

### VideoRecorder
Responsibilities:
- start/stop recording
- emit timestamps and file references
- remain optional/configurable

### SessionStore
Responsibilities:
- append runtime events
- save metadata for replay and offline analysis

---

## Content Architecture

Recommended source-of-truth structure:
- POI metadata
- route definitions
- narration variants
- FAQ snippets
- optional pre-generated audio

Suggested layout:
- `content/poi/*.yaml`
- `content/routes/*.yaml`
- `content/scripts/*.yaml`
- `content/faq/*.yaml`

The LLM should consume structured content, not replace it.

---

## Cross-Platform Design

### Desktop Dev
- allows fast testing with mock adapters
- may use larger debug tooling
- should not become the architecture baseline for deployment assumptions

### Isaac Sim
- connected through adapter interfaces
- primary purpose is pose-driven application validation
- simulation specifics must not leak into the core layer

### Orin NX / Embedded Edge
- resource-aware runtime
- reduced service count where needed
- configurable inference backend
- optional disablement of non-critical subsystems
- avoid giant dependency chains

### Android Client
- should interact with a stable backend API
- backend should not assume desktop browser-only use
- prioritize simple stateful APIs and touch-first workflows

---

## Configuration Strategy

Use environment-specific configuration files rather than code forks:
- `configs/dev.yaml`
- `configs/sim.yaml`
- `configs/edge.yaml`

Configurable dimensions should include:
- pose provider
- LLM backend
- TTS backend
- recording mode
- UI backend host/port
- performance mode
- logging verbosity

---

## Deployment Strategy Direction

Preferred pattern:
- keep hardware-dependent pieces on host where practical
- containerize backend/services when useful
- do not force full containerization early if it hurts device integration
- preserve the same API boundaries across platforms

---

## Logging and Observability

Minimum categories:
- pose/POI trigger logs
- orchestrator state transition logs
- narration events
- user Q&A events
- recording start/stop
- system health
- session identifiers

Every session should produce a consistent trace that supports replay and offline inspection.

---

## Architecture Guardrails

Do not:
- hardcode ROS topics inside core business logic
- hardcode Jetson-specific paths into orchestration logic
- put Isaac Sim-only semantics into the core layer
- let UI call directly into low-level adapters without backend mediation
- let the LLM become the raw knowledge owner

Do:
- define interfaces first
- keep adapters thin
- keep configs explicit
- prefer testable core modules
- protect embedded compatibility as a design constraint
