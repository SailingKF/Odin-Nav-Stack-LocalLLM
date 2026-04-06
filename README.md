<p align="center">
  <h2 align="center">Odin Navigation Stack</h2>
</p>

<div align="center">
  <a href="https://ManifoldTechLtd.github.io/Odin-Nav-Stack-Webpage">
  <img src='https://img.shields.io/badge/Webpage-OdinNavStack-blue' alt='webpage'></a>  
  <a href="https://www.apache.org/licenses/LICENSE-2.0">
  <img src='https://img.shields.io/badge/License-Apache2.0-green' alt='Apache2.0'></a>  
  <a href="https://www.youtube.com/watch?v=du038MPxc0s">
  <img src='https://img.shields.io/badge/Video-YouTube-red' alt='youtube'></a>  
  <a href="https://www.bilibili.com/video/BV1sFBXBmEum/">
  <img src='https://img.shields.io/badge/Video-bilibili-pink' alt='bilibili'></a>  
  <a href="https://wiki.ros.org/noetic">
  <img src='https://img.shields.io/badge/ROS-Noetic-orange' alt='noetic'></a>
</div>

**Odin1** is a high-performance spatial sensing module that delivers **high-precision 3D mapping**, **robust relocalization**, and rich sensory streams including **RGB images**, **depth**, **IMU**, **odometry**, and **dense point clouds**. Built on this foundation, we have developed various robotic intelligence stacks for ground platforms like the **Unitree Go2**, enabling:

- **Autonomous navigation with high-efficiency dynamic obstacle avoidance**  
- **Semantic object detection + natural-language navigation**  
- **Vision-Language Model (VLM) scene understanding and description**  

## Key Features

- **High-Accuracy SLAM & Persistent Relocalization** (inside Odin1, not open-sourced)  
  Real-time mapping with long-term relocalization using compact binary maps.
- **Dynamic Obstacle-Aware Navigation** (fully open-sourced)  
  Reactive local planners combined with global path planning for safe, smooth motion in complicated environments.
- **Semantic Navigation** (fully open-sourced)  
  Detect, localize, and navigate to objects using spoken or typed commands (e.g., _“Go to the left of the chair”_).
- **Vision-Language Integration** (fully open-sourced)  
  Generate contextual scene descriptions in natural language using multimodal AI.
- **Modular, ROS1-Based Architecture**  
  Easy to extend, customize, and integrate into your own robotic applications.

## Local LLM Tour Guide Extension

This repository is also being extended with a location-triggered tour guide application layer built on top of Odin Nav Stack, with a focus on:

- map point / POI triggered explanations and guided narration
- local LLM based explanation and follow-up Q&A
- Android-friendly control and debug UI
- deployment compatibility for embedded platforms such as Jetson Orin NX

Foundation docs for this extension live in [`docs/`](docs/):

- [PROJECT](docs/PROJECT.md)
- [ARCHITECTURE](docs/ARCHITECTURE.md)
- [DEV_WORKFLOW](docs/DEV_WORKFLOW.md)
- [DEPLOYMENT](docs/DEPLOYMENT.md)
- [AGENT](docs/AGENT.md)

## Mock Tour Foundation

This iteration adds a laptop-first mock tour skeleton without depending on Odin hardware, Isaac Sim, Android UI, or a real LLM runtime.

What is included:
- lightweight environment configs in `configs/`
- platform-neutral core interfaces in `core/interfaces/`
- POI loading and trigger logic in `core/poi/`
- a minimal tour state machine in `core/tour_orchestrator/`
- JSONL session logging in `core/session/`
- a mock pose adapter and runnable demo script in `adapters/mock/` and `scripts/run_mock_tour.py`

How to run:
```shell
python scripts/run_mock_tour.py
python -m unittest discover -s tests
```

Current limitations:
- narration is printed only, with no TTS
- no Android control surface yet
- no Isaac Sim, ROS, or Odin pose adapter integration yet
- no real local LLM, ASR, or video recording pipeline in this bundle

Planned extension path:
- replace the mock pose provider with Isaac Sim and ROS/Odin adapters through the same interfaces
- keep the core tour logic unchanged when moving to Orin NX
- add an Android-friendly backend and UI on top of the same session and orchestrator flow

## Local API Control Layer

This iteration adds a lightweight FastAPI backend in `services/api_server/` so an Android browser or H5 debug client can control the mock tour without coupling UI logic into the core modules.

What is included:
- FastAPI app factory in `services/api_server/app.py`
- runtime wrapper for mock tour control in `services/api_server/runtime.py`
- control endpoints for health, state, start, pause, resume, next, and latest session
- a new startup entrypoint in `scripts/run_api_server.py`

How to start the local API service:
```shell
python scripts/run_api_server.py
```

Example calls:
```shell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/state
curl -X POST http://127.0.0.1:8000/tour/start
curl -X POST http://127.0.0.1:8000/tour/pause
curl -X POST http://127.0.0.1:8000/tour/resume
curl -X POST http://127.0.0.1:8000/tour/next
curl http://127.0.0.1:8000/session/latest
```

Why this structure fits Android and Orin NX:
- the backend remains thin and platform-agnostic
- the core tour logic still lives under `core/`
- the mock pose source still lives under `adapters/mock/`
- the API surface is simple enough for Android browser or H5 tooling
- the dependency footprint stays small enough for future Orin NX deployment

Current API limitations:
- only the mock pose provider is wired to the API in this round
- the control flow uses a minimal background loop, not a full scheduler
- there is still no TTS, ASR, real LLM, video recorder, Isaac Sim, or ROS/Odin integration
- the API provides JSON control and inspection only, not a rendered web page

## Android-Friendly Debug Page

This iteration adds a very thin H5 debug panel in `services/api_server/static/` and serves it from the existing FastAPI process.

What is included:
- a mobile-friendly page at `/debug`
- large touch buttons for start, pause, resume, next, and refresh
- panels for health, current state, route progress, and latest session
- a configurable API base URL field so Android can target a laptop or Orin NX over LAN
- optional polling-based auto refresh with no frontend framework or build step

How to start the API and debug page:
```shell
python scripts/run_api_server.py
```

Open the page:
- local laptop browser: `http://127.0.0.1:8000/debug`
- Android browser over LAN: `http://<device-ip>:8000/debug`

Android access notes:
- start the server with the default `0.0.0.0` binding from `scripts/run_api_server.py`
- find the IP of the laptop or Orin NX on the same network
- open `http://<that-ip>:8000/debug` on the phone
- inside the page, either set the API base URL manually or tap `Use Page Origin`

Why this structure fits Orin NX + Android debugging:
- the page is static HTML/CSS/JS, so it adds almost no runtime complexity
- the FastAPI backend stays the single integration point
- there is no heavy frontend toolchain to drag into edge deployment
- the same page works from desktop and Android browser with only a URL change

Current debug page limitations:
- it consumes the existing mock-tour API only
- it uses polling rather than websockets or complex state sync
- there is still no native Android app, no TTS/ASR, and no real hardware integration

## Structured Content And Narrator Layer

This iteration upgrades the narration path from a single fixed `narration_text` field to a structured POI content library plus a narrator abstraction.

Structured POI content now includes:
- `spot_id`
- `name`
- `x`
- `y`
- `trigger_radius`
- `short_text`
- `standard_text`
- `extended_text`
- `facts`
- `faq`
- optional `tags`
- optional `persona`
- optional `theme`

The narrator abstraction lives in `core/interfaces/narrator.py` and is implemented by:
- `core/narrator/mock_narrator.py`
- `core/narrator/local_llm_narrator.py`

How narrator modes work:
- `short`: brief mobile-friendly summary
- `standard`: default guided explanation
- `extended`: longer explanation with richer detail and facts

Configuration knobs:
- `narrator_type: mock | local_llm`
- `narration_mode_default: short | standard | extended`
- `llm_gateway_url: http://127.0.0.1:9000`

Mode switching examples:
```yaml
narrator_type: mock
narration_mode_default: standard
```

```yaml
narrator_type: local_llm
narration_mode_default: extended
llm_gateway_url: http://127.0.0.1:9000
```

Current LocalLLMNarrator status:
- it is a lightweight client abstraction, not a heavy model runtime
- it can call a local HTTP gateway through `llm_gateway_url`
- if the gateway is unavailable, it falls back to `MockNarrator`

Local gateway scaffold:
- `services/llm_gateway/app.py`
- `scripts/run_llm_gateway.py`

Run the local gateway scaffold:
```shell
python scripts/run_llm_gateway.py
```

Why this structure fits future Gemma 4 and Orin NX:
- the orchestrator no longer knows how narration is produced
- structured content remains the source of truth
- the mock narrator is enough for laptop and API/debug validation
- the LocalLLMNarrator can point to a lightweight on-device Gemma 4 service later
- the LLM runtime can evolve independently from the core tour flow

API/debug page additions in this round:
- state now exposes narrator type, narration mode, current narration text, and latest answer text
- `POST /tour/question` supports minimal follow-up Q&A
- `/debug` now includes a small question box and answer panel

Current limitations:
- the local LLM path is still scaffold-level and uses a mock backend by default
- no TTS/ASR or spoken interaction yet
- no conversation memory beyond the active or last narrated POI
- no hardware adapters or simulator-specific narrator tuning yet

## Local LLM Gateway Backends

The local LLM gateway now supports two backend modes:
- `mock`
- `ollama`

Gateway health now reports:
- gateway status
- configured backend type
- active backend type
- model name
- fallback enabled / active state

Relevant config fields:
- `llm_backend_type`
- `llm_model_name`
- `llm_base_url`
- `llm_timeout_sec`
- `llm_enable_fallback`
- `llm_gateway_url`

Recommended development flow:
1. keep `narrator_type: mock` for the safest default
2. start the gateway in `mock` backend mode for API validation
3. switch `narrator_type: local_llm` when you want the API server to call the gateway
4. switch `llm_backend_type: ollama` when a local Ollama runtime and a local Gemma model are available

Example gateway startup:
```shell
python scripts/run_llm_gateway.py --config configs/dev.yaml
```

Example local-LLM oriented config:
```yaml
narrator_type: local_llm
llm_gateway_url: http://127.0.0.1:9000
llm_backend_type: ollama
llm_model_name: gemma3:4b
llm_base_url: http://127.0.0.1:11434
llm_timeout_sec: 60.0
llm_enable_fallback: true
```

Quick local runtime check on Windows:
```shell
"C:\Users\<you>\AppData\Local\Programs\Ollama\ollama.exe" --version
"C:\Users\<you>\AppData\Local\Programs\Ollama\ollama.exe" list
curl http://127.0.0.1:11434/api/tags
```

Recommended first local model:
- `gemma3:4b`

Why `gemma3:4b` first:
- easier to pull and verify than a larger Gemma variant
- enough to validate narration and follow-up Q&A through the existing gateway
- keeps the local development path closer to what we can later trim for edge deployment

If the model is missing, pull it with:
```shell
"C:\Users\<you>\AppData\Local\Programs\Ollama\ollama.exe" pull gemma3:4b
```

How to verify real local output through the project:
1. Start the local model runtime and confirm `gemma3:4b` appears in `/api/tags`
2. Start the gateway:
   `python scripts/run_llm_gateway.py --config configs/dev.yaml`
3. Confirm `/health` reports `configured_backend_type=ollama`, `active_backend_type=ollama`, and `fallback_active=false`
4. Start the API server:
   `python scripts/run_api_server.py`
5. Open `http://127.0.0.1:8000/debug`
6. Start the tour and ask a follow-up question

If the local model is unavailable:
- the gateway health becomes `degraded`
- the narrator falls back to mock output if fallback is enabled
- the API and `/debug` page stay usable for control-path validation

How real local model integration works:
- `LocalLLMNarrator` calls the HTTP gateway
- the gateway chooses the configured backend adapter
- the `ollama` backend builds a constrained prompt from structured POI content
- the prompt is sent to the local Ollama HTTP API
- if the backend is unavailable and fallback is enabled, the gateway or narrator falls back to mock behavior

Prompting approach:
- narration uses POI name, mode, short/standard/extended text, facts, tags, persona, and theme
- follow-up answers use the current POI FAQ, facts, and base text
- prompts explicitly tell the model to stay within the supplied content

Focused prompt/content contract:
- `docs/LLM_PROMPT_CONTRACT.md`

Ollama / Gemma note:
- this repository does not hardcode one exact Gemma runtime tag
- set `llm_model_name` to the model tag that exists in your local runtime
- if Ollama is not installed or the model is missing, `/health` will report a degraded state and fallback can keep the route alive

## Audio Output Boundary

This iteration introduces a platform-agnostic audio output contract so narration and follow-up answers can flow through an explicit playback path before we choose a real TTS engine.

What is included:
- core audio interface in `core/interfaces/audio_output.py`
- development adapters in `adapters/mock/audio_output.py`
- orchestrator wiring so narration and answer text both request playback
- session and state fields that expose playback activity

Config knob:
```yaml
audio_output_type: tts_service
tts_backend_type: mock
tts_artifact_dir: session_logs/dev_tts_artifacts
```

Current development modes:
- `mock`: records playback requests and prints lightweight `[AUDIO]` traces
- `silent`: keeps the flow intact but marks playback as skipped
- `tts_service`: routes playback through the service-layer TTS contract and returns synthesis artifact metadata

How to validate quickly:
```shell
python scripts/run_mock_tour.py
python -m unittest tests.test_audio_output -v
```

What you should see during a run:
- normal narration text output
- `[AUDIO] narration via mock: ...`
- `[AUDIO] answer via mock: ...`
- session state containing `last_audio_playback`

Focused contract doc:
- `docs/AUDIO_OUTPUT_CONTRACT.md`
- `docs/TTS_SERVICE_CONTRACT.md`
- `docs/AUDIO_PLAYBACK_POLICY.md`

What still remains before real spoken playback:
- choosing a TTS backend
- queueing / interrupt behavior
- audio device selection
- waveform or stream generation

## TTS Service Baseline

This iteration adds a service-layer synthesis contract under `services/tts_service/` so the audio path can be structured like a real TTS pipeline without committing to an engine yet.

What is included:
- `services/tts_service/service.py` with request/response/artifact types
- a deterministic `MockTTSBackend`
- a service-backed audio output mode that calls the TTS service
- artifact-aware playback metadata in runtime state and session summaries

Current service-backed behavior:
- synthesis writes a lightweight JSON artifact instead of an audio waveform
- playback metadata reports:
  - active backend type
  - synthesis status
  - estimated duration
  - artifact URI, kind, mime type, and content hash

## Artifact Player Backend Baseline

This iteration adds an explicit playback backend seam after synthesis so service-backed audio no longer treats a synthesized artifact as implicitly playable.

What is included:
- `adapters/mock/artifact_player.py`
- a `MockArtifactPlayerBackend`
- service-backed audio start routed through `start_artifact(...)`
- service-backed interruption routed through `interrupt_handle(...)`

Current config knob:
```yaml
artifact_player_backend_type: mock
```

What runtime and session metadata now show:
- synthesis ownership:
  - `tts_backend_type`
  - `tts_status`
  - `artifact`
- playback backend ownership:
  - `playback_backend_type`
  - `playback_handle`
  - `player_start_hook_invoked`
  - `player_interrupt_hook_invoked`

## Playback Completion Signal Baseline

This iteration adds a backend-side completion reporting seam so service-backed playback no longer relies only on estimated duration inside the lifecycle manager.

What is included:
- playback backend state polling through `get_handle_state(...)`
- service-backed completion rollover driven by backend-reported handle status
- estimated fallback completion for modes that do not expose backend-side completion

What runtime metadata now makes visible:
- `playback_completion_supported`
- `playback_completion_source`
- `latest_playback_handle_status`
- `playback_completion_observation`

What `playback_completed` events now distinguish:
- `completion_source: "backend_reported"`
- `completion_source: "estimated_fallback"`

Focused contract docs:
- `docs/ARTIFACT_PLAYER_BACKEND.md`
- `docs/AUDIO_PLAYBACK_POLICY.md`

## Playback Failure And Degraded Continuation Baseline

This iteration adds a narrow playback-failure seam for service-backed playback and defines one explicit degraded continuation policy.

Chosen degraded policy:
- mark the failed playback item as failed
- record failure metadata in lifecycle state
- continue the queue instead of stalling the whole audio path

Failure cases now modeled:
- playback start failure before an item becomes active
- active service-backed playback later reporting `failed`

What runtime metadata now makes visible:
- `playback_failure_source`
- `failure_status`
- `failure_message`
- `degraded_continuation_applied`
- `degraded_continuation_policy`
- `playback_failure_observation`

What `playback_failed` events now distinguish:
- `failure_source: "start_failed"`
- `failure_source: "backend_reported"`

## Audio Observability Surface Baseline

This iteration adds a concise audio summary on top of the raw playback lifecycle state so operators can quickly inspect audio behavior from the API and `/debug` page.

New summary surfaces now expose:
- active playback status
- active playback kind / output type
- queued count
- latest completion source
- latest failure source and status
- whether degraded continuation was applied
- latest handle status

Where the summary is now visible:
- `GET /state` as `audio_summary`
- `GET /session/latest` as `audio_summary`
- `/debug` in the new `Audio Summary` panel

What still remains raw-only:
- detailed lifecycle event history
- full active / queued playback item metadata
- recent low-level backend observations in `audio_playback_state`

Focused contract docs:
- `docs/TTS_SERVICE_CONTRACT.md`
- `docs/ARTIFACT_PLAYER_BACKEND.md`
- `docs/AUDIO_PLAYBACK_POLICY.md`

## Deployment Capability Profiles

This iteration adds a narrow deployment capability/profile layer so the repo can state what `dev`, `sim`, and `edge` currently mean without scattering environment checks across the codebase.

What is included:
- a profile/validation seam in `services/deployment_profile/profile.py`
- API-visible `deployment_profile` summaries in runtime health/state surfaces
- focused validation for obvious profile mismatches and placeholder/mock settings

Current profile intent:
- `dev`: laptop-first, mock pose, fast iteration, API/debug validation
- `sim`: simulator ingress path, sim-first integration, optional stub/live Isaac source
- `edge`: Orin/robot-oriented shape, local LLM expected, real pose/audio still allowed to be placeholder for now

What the profile summary now reports:
- deployment class such as `dev_only`, `sim_only`, or `edge_candidate`
- readiness state such as `ready_for_profile`, `placeholder`, or `invalid`
- expected pose / LLM / audio / recording shape
- active mock-only components
- placeholder components that still block true edge readiness
- validation warnings and errors for obvious mismatches

Current edge placeholders in this repo:
- `audio_output_type: mock`
- `tts_backend_type: mock`
- `artifact_player_backend_type: mock`

How to inspect it:
```shell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/state
```

Look for:
- `deployment_profile.profile_name`
- `deployment_profile.readiness_status`
- `deployment_profile.mock_components_active`
- `deployment_profile.placeholder_components`

Focused contract doc:
- `docs/DEPLOYMENT_PROFILE_CONTRACT.md`
- `docs/DEPLOYMENT.md`

## Deployment Preflight And Dependency Probe

This iteration adds a thin startup-time preflight layer on top of the deployment profile summary.

What it does:
- checks whether configured route and POI files exist
- checks whether the configured session log directory can be created and written
- probes local HTTP dependencies with short timeouts when safe
- explicitly labels dependencies that remain external or unverified

Current API-visible surface:
- `deployment_preflight`

Current per-check statuses:
- `ok`
- `unreachable`
- `missing`
- `unverified_external`
- `not_applicable`

Current safe probes:
- `llm_gateway` via `/health` when `narrator_type: local_llm`
- `ollama_runtime` via `/api/tags` when `llm_backend_type: ollama`

Current external/unverified markers include:
- `hardware_pose_dependency` for `pose_provider_type: odin_ros`
- `isaac_live_dependency` for live simulator mode
- `audio_device_dependency` for non-mock audio paths

How to inspect it:
```shell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/state
```

What this preflight does not prove:
- that ROS/Odin hardware is actually publishing
- that a real audio device path works end-to-end
- that live Isaac integration is attached and producing poses
- that a reachable LLM runtime is fully correct for deployment

Focused contract docs:
- `docs/DEPLOYMENT_PREFLIGHT_CONTRACT.md`
- `docs/DEPLOYMENT_PROFILE_CONTRACT.md`

## Deployment Launch Plan And Startup Contract

This iteration adds a narrow launch-plan/startup-contract layer so the repo can describe what should start, in what order, and which steps are repo-owned versus external/manual.

Current API-visible surface:
- `deployment_launch_plan`

Current step categories:
- `internal_service`
- `external_dependency`
- `optional_service`

Current startup expectations are now represented per profile:
- `dev`
  - external Ollama runtime when configured
  - repo-owned llm gateway
  - repo-owned API server
  - optional `/debug` browser client
- `sim`
  - stub or live simulator source decision
  - repo-owned sim pose ingress server
  - optional publisher bridge
  - optional API/debug server
- `edge`
  - external hardware pose dependency
  - external LLM runtime when configured
  - repo-owned llm gateway
  - repo-owned API server
  - future/manual audio-device step when edge leaves mock audio

How operators can inspect it now:
```shell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/state
python scripts/print_launch_plan.py --config configs/dev.yaml
python scripts/print_launch_plan.py --config configs/edge.yaml
```

What this does not automate:
- process supervision
- restart logic
- systemd/service packaging
- real hardware bring-up

Focused contract doc:
- `docs/DEPLOYMENT_LAUNCH_PLAN_CONTRACT.md`

## Deployment Readiness Report And Blocking Summary

This iteration adds a narrow readiness aggregation layer that combines:
- `deployment_profile`
- `deployment_preflight`
- `deployment_launch_plan`

into one operator-facing readiness report.

Current runtime-visible surface:
- `deployment_readiness`

Current per-step readiness states:
- `ready`
- `blocked`
- `optional`
- `external_unverified`
- `not_applicable`

Current overall readiness states:
- `blocked`
- `external_verification_needed`
- `ready_for_guided_bringup`
- `ready_with_placeholders`

What this makes easier to see:
- which required startup steps are currently ready
- which required steps are blocked by missing or unreachable dependencies
- which steps remain optional
- which steps remain external and only partially verifiable

How to inspect it now:
```shell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/state
python scripts/print_readiness_report.py --config configs/dev.yaml
python scripts/print_readiness_report.py --config configs/edge.yaml
```

What this still does not do:
- auto-start services
- supervise processes
- prove real hardware pose or audio readiness

Focused contract doc:
- `docs/DEPLOYMENT_READINESS_CONTRACT.md`

## Deployment Command Manifest And Guided Bring-Up Sheet

This iteration adds a narrow command-manifest layer that turns repo-owned startup steps into explicit commands for `dev`, `sim`, and `edge`.

Current runtime-visible surface:
- `deployment_command_manifest`

What this makes easier to see:
- which launch-plan steps map to repo-owned commands
- which steps remain manual or external
- which config each repo-owned command should use
- the exact command string to run in launch order

Current repo-owned command mapping examples:
- `llm_gateway`
  - `python scripts/run_llm_gateway.py --config configs/dev.yaml`
- `api_server`
  - `python scripts/run_api_server.py --config configs/dev.yaml`
- `sim_pose_ingress_server`
  - `python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml`

Current manual or external examples with no repo command:
- `ollama_runtime`
- `hardware_pose_dependency`
- `debug_browser`

How to inspect it now:
```shell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/state
python scripts/print_bringup_sheet.py --config configs/dev.yaml
python scripts/print_bringup_sheet.py --config configs/edge.yaml
```

What this still does not do:
- auto-start services
- supervise long-running processes
- replace real deployment packaging

Focused contract doc:
- `docs/DEPLOYMENT_COMMAND_MANIFEST_CONTRACT.md`

## Deployment Verification Manifest And Success Checks

This iteration adds a narrow verification-manifest layer that makes post-start success checks explicit for repo-owned services.

Current runtime-visible surface:
- `deployment_verification_manifest`

What this makes easier to see:
- how to verify a repo-owned service after it is started
- which health endpoint or runtime surface should be inspected
- what fields count as a successful response for API server, LLM gateway, and sim ingress service
- which steps remain manual or external and therefore have no repo verification contract

Current verification mapping examples:
- `llm_gateway`
  - `GET http://127.0.0.1:9000/health`
  - expect fields such as `service`, `active_backend_type`, and `fallback_active`
- `api_server`
  - `GET http://127.0.0.1:8000/health`
  - expect fields such as `service`, `env_name`, and `deployment_profile`
- `sim_pose_ingress_server`
  - `GET http://127.0.0.1:8100/health`
  - expect fields such as `service`, `ingress_contract`, and `deployment_profile`

Current manual or external steps with no repo verification contract:
- `hardware_pose_dependency`
- `ollama_runtime`
- `debug_browser`

How to inspect it now:
```shell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/state
python scripts/print_verification_sheet.py --config configs/dev.yaml
python scripts/print_verification_sheet.py --config configs/edge.yaml
```

What this still does not do:
- wait for services to come up
- poll endpoints continuously
- supervise processes

Focused contract doc:
- `docs/DEPLOYMENT_VERIFICATION_MANIFEST_CONTRACT.md`

## Deployment Verification Runner And Result Summary

This iteration adds a narrow one-shot verification runner that executes the existing repo-owned verification manifest checks once and produces a concrete result summary.

Current operator-facing entry point:
- `python scripts/run_verification_summary.py --config configs/<profile>.yaml`

What this makes easier to see:
- which repo-owned verification checks passed
- which checks failed because the target was unreachable
- which checks failed because the response status was wrong
- which checks failed because expected fields were missing
- which steps were manual or external and therefore skipped

Current result statuses:
- `passed`
- `failed_unreachable`
- `failed_invalid_status`
- `failed_missing_fields`
- `failed_invalid_payload`
- `failed_unsupported_kind`
- `manual_external`
- `manual_optional`

Current overall summary statuses:
- `passed`
- `failed`
- `manual_only`

Example usage:
```shell
python scripts/run_verification_summary.py --config configs/dev.yaml
python scripts/run_verification_summary.py --config configs/edge.yaml --timeout-sec 1.5
```

What this still does not do:
- start services
- wait until services become healthy
- retry checks
- poll continuously

Focused contract doc:
- `docs/DEPLOYMENT_VERIFICATION_RUNNER_CONTRACT.md`

## Deployment Endpoint Contract And Config-Driven Targets

This iteration adds a narrow endpoint-contract layer so repo-owned service URLs and ports derive from one explicit source instead of being re-typed across command and verification layers.

Current runtime-visible surface:
- `deployment_endpoint_contract`

What this makes easier to see:
- which host and port each repo-owned internal service assumes
- which values currently come from config
- which values currently fall back to defaults
- how command argv and verification URLs stay aligned

Current services covered:
- `llm_gateway`
- `api_server`
- `sim_pose_ingress_server`

Current derivation behavior:
- `llm_gateway`
  - verification/command target derives from `llm_gateway_url` when configured
- `api_server`
  - defaults to `0.0.0.0:8000` bind with `http://127.0.0.1:8000` local connect URL unless overridden
- `sim_pose_ingress_server`
  - defaults to `127.0.0.1:8100` unless overridden

How to inspect it now:
```shell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/state
python scripts/print_endpoint_contract.py --config configs/dev.yaml
python scripts/print_endpoint_contract.py --config configs/edge.yaml
```

Example optional config override shape:
```yaml
service_endpoints:
  api_server:
    bind_host: 0.0.0.0
    connect_host: 127.0.0.1
    port: 8088
```

Preferred endpoint config shape:
```yaml
service_endpoints:
  llm_gateway:
    bind_host: 0.0.0.0
    connect_host: 127.0.0.1
    port: 9000
    scheme: http
```

Current precedence rules:
1. `service_endpoints.<service_id>`
2. legacy compatibility field such as `llm_gateway_url`
3. built-in default

What this still does not do:
- dynamic service discovery
- reverse proxying
- startup automation

Focused contract doc:
- `docs/DEPLOYMENT_ENDPOINT_CONTRACT.md`
- `docs/DEPLOYMENT_ENDPOINT_CONFIG_CANONICALIZATION.md`

## Deployment Config Hygiene Summary

This iteration adds a narrow endpoint config-hygiene layer on top of the canonical endpoint contract so operators can see migration/deprecation status without reading code.

Current runtime-visible surface:
- `deployment_config_hygiene`

What it now makes explicit:
- whether a profile is `fully_canonicalized`, `partially_canonicalized`, `mixed_canonical_and_legacy`, `legacy_dependent`, or `default_heavy`
- whether deprecated fields such as `llm_gateway_url` are merely present or still actively in use
- what migration action is recommended next for each repo-owned service

How to inspect it now:
```shell
python scripts/print_config_hygiene.py --config configs/dev.yaml
python scripts/print_config_hygiene.py --config configs/sim.yaml
python scripts/print_config_hygiene.py --config configs/edge.yaml
```

Migration intent in this round:
- keep backward compatibility
- prefer `service_endpoints.<service_id>` as the canonical config shape
- surface legacy/deprecation cleanup as guidance, not as a breaking change

Focused contract doc:
- `docs/DEPLOYMENT_CONFIG_HYGIENE.md`

## MVSim Minimal Integration

This iteration adds a narrow MVSim-oriented compatibility path for PC-side end-to-end simulation without bringing in Isaac.

What is included:
- an MVSim-style planar observation source in `services/sim_publisher_bridge/mvsim_source.py`
- a sample observation stream in `content/sim/demo_mvsim_pose_stream.yaml`
- a runnable bridge demo in `scripts/run_mvsim_compat_bridge_demo.py`
- a sim-aware API proxy mode so `python scripts/run_api_server.py --config configs/sim.yaml` can keep serving `/debug` while observing the running sim-ingress runtime

What is real in this round:
- real HTTP ingress through `/runtime/start`, `/poses/batch`, and `/stream/finish`
- real tour/session/narration behavior downstream of sim-ingress
- real `/debug`-backed API observation through the sim-profile API server

What remains compatibility scaffolding:
- the current MVSim path replays MVSim-style planar observations from a file
- it does not yet claim a direct live MVSim process/runtime integration

PC validation flow:
```shell
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
python scripts/run_api_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8000
python scripts/run_mvsim_compat_bridge_demo.py --config configs/sim.yaml --base-url http://127.0.0.1:8100
```

Open the debug page:
- `http://127.0.0.1:8000/debug`

Focused doc:
- `docs/MVSIM_MINIMAL_INTEGRATION.md`

## MVSim Guided Validation Harness

This iteration adds a PC-only operator validation harness so a human can validate the current MVSim compatibility path from one local page instead of coordinating multiple terminals and ad hoc API calls.

What is included:
- a local harness runtime in `services/mvsim_validation_harness/`
- a simple local page at `/harness`
- narrow attach-or-launch behavior for:
  - sim pose ingress
  - sim-profile API server
- one-click MVSim validation that runs the bridge demo and summarizes:
  - service health
  - `/debug` reachability
  - route completion
  - latest session id
  - latest narration
  - follow-up question result

Easiest human flow:
```shell
python scripts/run_mvsim_validation_harness.py --config configs/sim.yaml --open-browser
```

Then use the local page:
- `Start / Attach Local Stack`
- `Run MVSim Validation`
- `Open /debug`

What this harness is not:
- not a general supervisor
- not a packaging/service-manager layer
- not direct live MVSim integration

Focused doc:
- `docs/MVSIM_VALIDATION_HARNESS.md`

How to validate the service-backed path:
```shell
python scripts/run_mock_tour.py
python -m unittest tests.test_tts_service -v
```

What you should see:
- `[AUDIO] narration via artifact_player/mock: ...`
- `[AUDIO] answer via artifact_player/mock: ...`
- `latest_audio_playback.extra.metadata.backend_type == "mock"`
- a generated mock synthesis artifact under the configured `tts_artifact_dir`

## Audio Queue And Interruption Policy

This iteration adds a minimal playback lifecycle policy on the audio-output side so overlapping requests behave predictably before we choose a real playback engine.

Chosen policy:
- narration requests queue in FIFO order when something is already active
- answer requests interrupt and replace the active playback immediately

Lifecycle model:
- request accepted and prepared
- playback started
- playback interrupted or replaced
- playback completed

Observable runtime state:
- `audio_playback_state.policy_name`
- `audio_playback_state.active_playback`
- `audio_playback_state.queued_playbacks`
- `audio_playback_state.recent_events`

Quick overlap validation:
```shell
python scripts/run_audio_overlap_demo.py
```

What you should see:
- first narration is `prepared` and then `started`
- second narration is `prepared` and then `queued` with `start_hook_invoked: false`
- answer is `prepared`, then `replaced_active`, and the active narration emits a `playback_interrupted` event

Focused policy doc:
- `docs/AUDIO_PLAYBACK_POLICY.md`

# Quick Start

The code has been tested on:
- OS: Ubuntu 20.04  
- ROS: ROS1 Noetic  
- Robot Platform: Unitree Go2  
- Hardware: NVIDIA Jetson (Orin Nano) or x86 with GPU


## 1. Clone the Repository

``` shell
git clone --depth 1 --recursive https://github.com/ManifoldTechLtd/Odin-Nav-Stack.git
```

The Odin1 driver may need to update:
``` shell
cd Odin-Nav-Stack/ros_ws/src/odin_ros_driver
git fetch origin
git checkout main
git pull origin main
```

### Odin1 ROS driver modification

We need to modify certain features of the odin1 ROS driver to adapt it for navigation, which may cause conflicts with your other programs.

Please edit the `ros_ws/src/odin_ros_driver/include/host_sdk_sample.h`. Please note the location to modify. You should modify the ROS1 section, not the ROS2 section.

1. Modifiy the `ns_to_ros_time` function:
    ``` cpp
    inline ros::Time ns_to_ros_time(uint64_t timestamp_ns) {
        ros::Time t;
        #ifdef ROS2
            t.sec = static_cast<int32_t>(timestamp_ns / 1000000000);
            t.nanosec = static_cast<uint32_t>(timestamp_ns % 1000000000);
        #else
            // t.sec = static_cast<uint32_t>(timestamp_ns / 1000000000);
            // t.nsec = static_cast<uint32_t>(timestamp_ns % 1000000000);
            return ros::Time::now();
        #endif
        return t;
    }
    ```

2. Comment out the low-frequency TF transform in function `publishOdometry`:
    ``` cpp
    switch(odom_type) {
        case OdometryType::STANDARD:
            {
            // geometry_msgs::TransformStamped transformStamped;
            // transformStamped.header.stamp = msg.header.stamp;
            // transformStamped.header.frame_id = "odom";
            // transformStamped.child_frame_id = "odin1_base_link";
            // transformStamped.transform.translation.x = msg.pose.pose.position.x;
            // transformStamped.transform.translation.y = msg.pose.pose.position.y;
            // transformStamped.transform.translation.z = msg.pose.pose.position.z;
            // transformStamped.transform.rotation.x = msg.pose.pose.orientation.x;
            // transformStamped.transform.rotation.y = msg.pose.pose.orientation.y;
            // transformStamped.transform.rotation.z = msg.pose.pose.orientation.z;
            // transformStamped.transform.rotation.w = msg.pose.pose.orientation.w;
            // tf_broadcaster->sendTransform(transformStamped);
            odom_publisher_.publish(msg);
    ...
    ```

3. Add high-frequency TF transform publication in function `publishOdometry`:
    ``` cpp
    case OdometryType::HIGHFREQ:{
        geometry_msgs::TransformStamped transformStamped;
        transformStamped.header.stamp = msg.header.stamp;
        transformStamped.header.frame_id = "odom";
        transformStamped.child_frame_id = "odin1_base_link";
        transformStamped.transform.translation.x = msg.pose.pose.position.x;
        transformStamped.transform.translation.y = msg.pose.pose.position.y;
        transformStamped.transform.translation.z = msg.pose.pose.position.z;
        transformStamped.transform.rotation.x = msg.pose.pose.orientation.x;
        transformStamped.transform.rotation.y = msg.pose.pose.orientation.y;
        transformStamped.transform.rotation.z = msg.pose.pose.orientation.z;
        transformStamped.transform.rotation.w = msg.pose.pose.orientation.w;
        tf_broadcaster->sendTransform(transformStamped);
        odom_highfreq_publisher_.publish(msg);
        break;
    }
    ```

## 2. Install System Dependencies
``` shell
export ROS_DISTRO=noetic
sudo apt update
sudo apt install -y \
    ros-${ROS_DISTRO}-tf2-ros \
    ros-${ROS_DISTRO}-tf2-geometry-msgs \
    ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-tf2-eigen \
    ros-${ROS_DISTRO}-pcl-ros \
    ros-${ROS_DISTRO}-move-base \
    ros-${ROS_DISTRO}-dwa-local-planner
```

## 3. Install Unitree Go2 SDK
Follow the official guide:
[Unitree Go2 SDK](https://support.unitree.com/home/zh/developer/Obtain%20SDK?spm=a2ty_o01.29997173.0.0.737bc921PvkEw8)

## 4. Set Up Conda & Mamba 
Follow the installation in [miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install#basic-install-instructions).
``` shell
conda install -n base -c conda-forge mamba
# Re-login to your shell after installation
```

## 5. Create the NeuPAN Environment 
``` shell
export ROS_DISTRO=noetic
mamba create -n neupan -y
mamba activate neupan
conda config --env --add channels conda-forge
conda config --env --remove channels defaults
conda config --env --add channels robostack-${ROS_DISTRO}
mamba install -n neupan ros-${ROS_DISTRO}-desktop colcon-common-extensions catkin_tools rosdep ros-dev-tools -y
mamba run -n neupan pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
pip install -e NeuPAN
```

**For different Jetson users**: Replace the PyTorch install with a compatible .whl from [NVIDIA's Jeston PyTorch Page](https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048).

## 6. Build the ROS Workspace 

There are two methods for compiling workspaces: one involves using ROS within a conda environment, and the other involves ROS installed system-wide. If you need to compile using the system-installed ROS, ensure all conda environments are deactivated by running `mamba deactivate`.

### System-installed ROS build
``` shell
cd ros_ws
source /opt/ros/${ROS_DISTRO}/setup.bash
catkin_make -DCMAKE_BUILD_TYPE=Release
```

### Conda ROS build

Some packages need to be installed before compile
``` shell
mamba activate neupan
mamba install -c conda-forge -c robostack-noetic ros-noetic-pcl-ros ros-noetic-compressed-image-transport ros-noetic-compressed-depth-image-transport ros-noetic-image-transport
```

Compile:
``` shell
mamba activate neupan
cd ros_ws
catkin_make -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DPCL_VISUALIZATION=OFF -DQT_HOST_PATH=$CONDA_PREFIX
```

## 7. Set USB Rules for Odin1

``` shell
sudo vim /etc/udev/rules.d/99-odin-usb.rules
```

Add the following content to `/etc/udev/rules.d/99-odin-usb.rules`:

``` shell
SUBSYSTEM=="usb", ATTR{idVendor}=="2207", ATTR{idProduct}=="0019", MODE="0666", GROUP="plugdev"
```

Reload rules and reinsert devices
``` shell
sudo udevadm control --reload
sudo udevadm trigger
```

# Usage

- Mapping & Relocalization
- Navigation
- YOLO object detection
- VLM scene explanation

## Mapping and Relocalization with Odin1

Building maps and performing relocalization with Odin1

### 1. Configure Mapping Mode
Edit `ros_ws/src/odin_ros_driver/config/control_command.yaml`, set `custom_map_mode: 1` to enable mapping.

### 2. Launch Mapping 

Terminal 1 – Start Odin driver:
``` shell
source ros_ws/devel/setup.bash
roslaunch odin_ros_driver odin1_ros1.launch
```

Terminal 2 – Run mapping script:
``` shell
bash scripts/map_recording.sh awesome_map
```

The pcd map will be saved to `ros_ws/src/pcd2pgm/maps/` and the grid map will be saved to `ros_ws/src/map_planner/maps/`

After the map is constructed, you can view and modify the grid map using GIMP:
``` shell
sudo apt update && sudo apt install gimp
```

### 3. Relocalization & Navigation
Enable relocalization by editing `control_command.yaml`: 
``` shell
custom_map_mode: 2
relocalization_map_abs_path: "/abs/path/to/your/map"
```

Launch: 
``` shell
roslaunch odin_ros_driver odin1_ros1.launch
```

Verify TF tree: visualize TF tree in rqt: map → odom → odin1_base_link

Relocalization may require manually initiating motion.

## Navigation Modes
### Standard ROS Navigation (Not recommended, TODO)
Use Nav1 and move-base. Please [install](https://wiki.ros.org/navigation) before running.
``` shell
roslaunch navigation_planner navigation_planner.launch
```

### Custom Planner (Not recommended, TODO)
Tune `global_planner.yaml` and `local_planner.yaml` in `ros_ws/src/model_planner`, then:
``` shell
roslaunch model_planner model_planner.launch
```
You can modify the code and replace it with your own custom algorithm.

### End-to-End Neural Planner (Recommended)
This is our recommended high-performance local planner; please refer to the paper: [NeuPAN](https://ieeexplore.ieee.org/document/10938329/).

#### Model Training

If you are not using Unitree Go2, please train the dune model. Modify the training configuration file `NeuPAN/example/dune_train/dune_train_*.py` based on the chassis type, then run:
``` shell
cd NeuPAN/example/dune_train
python dune_train_*.py
```

Replace `*` with your chassis type. For more training detail, please refer to [here](https://github.com/hanruihua/NeuPAN?tab=readme-ov-file#dune-model-training-for-your-own-robot-with-a-specific-convex-geometry).

#### Launch
``` shell
# Terminal 1
roslaunch map_planner whole.launch

# Terminal 2
mamba activate neupan
python NeuPAN/neupan/ros/neupan_ros.py
```

Use RViz to publish 2D Nav Goals. Verify relocalization by visualize TF tree in rqt before publishing goal.

## Object detection

Enables navigation to specific objects. Requires depth maps and undistorted images from Odin1.

### 1. Install YOLOv5 in Virtual Environment:

First, install YOLOv5:
``` shell
python3 -m venv ros_ws/venvs/ros_yolo_py38
source ros_ws/venvs/ros_yolo_py38/bin/activate
pip install --upgrade pip "numpy<2.0.0"
cd ros_ws/src && git clone https://github.com/ultralytics/yolov5.git
pip install -r yolov5/requirements.txt
```
Please note that we encountered a conflict between the automatic installation of torch and torchvision on a certain Jetson Orin Nano. If you encounter this issue, please refer to the troubleshooting section.

Then, install other dependencies:
``` shell
pip install opencv-python pillow pyyaml requests tqdm scipy matplotlib seaborn pandas empy==3.3.4 catkin_pkg ros_pkg vosk sounddevice
```

Verify PyTorch and CUDA:
``` shell
python -c "import torch, torchvision; print('PyTorch:', torch.__version__); print('torchvision:', torchvision.__version__); print('CUDA available:', torch.cuda.is_available())"
```

Download resources:
``` shell
mkdir -p ros_ws/src/yolo_ros/scripts/voicemodel
cd ros_ws/src/yolo_ros/scripts/voicemodel
wget https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
unzip vosk-model-small-cn-0.22.zip
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt -O ../models/yolov5s.pt
chmod +x ../yolo_detector.py
```


### 2. Calibrate Camera 
Copy `Tcl_0` and `cam_0` from `odin_ros_driver/config/calib.yaml` into `yolo_detector.py`. 

### 3. Launch 
Terminal 1: 
``` shell
roslaunch odin_ros_driver odin1_ros1.launch
```

Terminal 2: 
``` shell
./run_yolo_detector.sh
```

In Terminal 2, you can enter the following commands to control it:
- list: Query recognized objects.
- object name: Display the 3D position in RViz.
- Move to the [Nth] [object] [direction]: Publish a navigation goal. (Supprot Chinese input)
- mode: Toggle between text and voice input.


## Vision-Language Model (VLM)
Install LLaMA.cpp:
``` shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install llama.cpp
```

Download models (e.g., SmolVLM):
``` shell
wget https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF/resolve/main/SmolVLM-500M-Instruct-Q8_0.gguf
wget https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF/resolve/main/mmproj-SmolVLM-500M-Instruct-Q8_0.gguf
```

### Launch

Terminal 1: 
``` shell
llama-server -m SmolVLM-500M-Instruct-Q8_0.gguf --mmproj mmproj-SmolVLM-500M-Instruct-Q8_0.gguf
```

Terminal 2:
``` shell
roslaunch odin_ros_driver odin1_ros1.launch
```

Terminal 3:
``` shell
roslaunch odin_vlm_terminal odin_vlm_terminal.launch
```

## VLN

### Launch

Terminal 1: 
``` shell
roslaunch map_planner whole.launch
```

Terminal 2:
``` shell
roslaunch odin_ros_driver odin1_ros1.launch
```

Terminal 3:
``` shell
mamba activate neupan
python NeuPAN/neupan/ros/neupan_ros.py
```

Terminal 4:
``` shell
mamba activate neupan
python scripts/str_cmd_control.py
```

Terminal 5:
``` shell
mamba activate neupan
python scripts/VLN.py
```

# FAQ

## How to check the status of relocalization

Open RViz, set `Global Options`-> `Fixed Frame` to map. In the bottom-left corner, select `Add` -> `By display type` -> `rviz` -> double-click `TF`. The appearance of the odom-map's coordinate axes and connections indicates successful relocalization.

## Start or goal is occupied after publishing the goal

If the start or end point is occupied, you can check the inflation map `/inflated_map` in RViz. The start and end points must lie outside the inflation area. Additionally, you can modify the inflation radius in `ros_ws/src/map_planner/launch/whole.launch:inflation_radius`.

## Unable to stop near the target point

This is a NeuPAN issue; there may be errors in reaching the target point. You can try increasing the `goal_tolerance` parameter in `ros_ws/src/map_planner/launch/whole.launch`.

If you have any other questions, you can post them on GitHub Issues.

# Troubleshooting

## torch conflict with torchvision
Error:`torch.cuda.is_available() returns False`

Cause: torchvision overwrote the CUDA-enabled PyTorch installation.

Fix:
``` shell
pip uninstall torch torchvision torchaudio
# Reinstall torch from .whl
pip install torch-*.whl
pip install --no-cache-dir "git+https://github.com/pytorch/vision.git@v0.16.0"
```
If the problem persists, you can try the following methods:
Navigate to `cd ros_ws/src/yolov5/utils`, open the `general.py` file, and locate the following code:
``` python
# Batched NMS
c = x[:, 5:6] * (0 if agnostic else max_wh)  # classes
boxes, scores = x[:, :4] + c, x[:, 4]  # boxes (offset by class), scores
i = torchvision.ops.nms(boxes, scores, iou_thres)  # NMS
```
Modify the YOLO code:
``` python
# Batched NMS (using pure PyTorch to avoid torchvision.ops compatibility issues)
c = x[:, 5:6] * (0 if agnostic else max_wh)  # classes
boxes, scores = x[:, :4] + c, x[:, 4]  # boxes (offset by class), scores
# Pure PyTorch NMS implementation
sorted_idx = torch.argsort(scores, descending=True)
keep = []
while len(sorted_idx) > 0:
    current_idx = sorted_idx[0]
    keep.append(current_idx)
    if len(sorted_idx) == 1:
        break
    current_box = boxes[current_idx:current_idx+1]
    rest_boxes = boxes[sorted_idx[1:]]
    # Calculate IoU
    inter_x1 = torch.max(current_box[:, 0], rest_boxes[:, 0])
    inter_y1 = torch.max(current_box[:, 1], rest_boxes[:, 1])
    inter_x2 = torch.min(current_box[:, 2], rest_boxes[:, 2])
    inter_y2 = torch.min(current_box[:, 3], rest_boxes[:, 3])
    inter_w = torch.clamp(inter_x2 - inter_x1, min=0)
    inter_h = torch.clamp(inter_y2 - inter_y1, min=0)
    inter_area = inter_w * inter_h
    current_area = (current_box[:, 2] - current_box[:, 0]) * (current_box[:, 3] - current_box[:, 1])
    rest_area = (rest_boxes[:, 2] - rest_boxes[:, 0]) * (rest_boxes[:, 3] - rest_boxes[:, 1])
    union_area = current_area + rest_area - inter_area
    iou = inter_area / union_area
    sorted_idx = sorted_idx[1:][iou < iou_thres]
i = torch.tensor(keep, dtype=torch.long, device=boxes.device)
``` 
 
## libgomp problem
Error: `libgomp` not found or similar problem

Cause: Missing installation or corrupted library files.

Fix:
``` shell
for f in ~/venvs/ros_yolo_py38/lib/python3.8/site-packages/torch.libs/libgomp*.so*; do
    [ -f "$f" ] && mv "$f" "$f.bak"
done
```

# Acknowledgements

Thanks to the excellent work by [ROS Navigation](https://github.com/ros-planning/navigation), [NeuPAN](https://github.com/hanruihua/NeuPAN), [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) and [Qwen](https://github.com/QwenLM/Qwen3-VL).

Special thanks to [hanruihua](https://github.com/hanruihua), [KevinLADLee](https://github.com/KevinLADLee) and [bearswang](https://github.com/bearswang) for their technical support.
