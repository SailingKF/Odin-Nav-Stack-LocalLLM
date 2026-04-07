# Current Round Prompt

## Round
Round 001 - Dev Laptop Local LLM Runtime Validation

## Goal
Connect the existing local LLM path to a real local runtime on the development machine and verify one end-to-end narration + Q&A flow.

## Why This Is The Current Priority

The project already has:
- mock tour loop
- API server
- Android-friendly `/debug` page
- structured POI content
- narrator abstraction
- LLM gateway with `mock` and `ollama` backends

The current critical path is to validate that the existing real-runtime integration actually works, not just the fallback path.

## In Scope

- install, start, or verify Ollama runtime only as needed for this round
- pull one Gemma-family model that is suitable for first validation on the dev machine
- use the existing `ollama` backend path in the repository
- make only minimal config or observability changes needed to verify the path
- verify:
  - Ollama runtime reachable
  - target model listed
  - gateway can call the model
  - `LocalLLMNarrator` receives real output
  - API and/or `/debug` can drive the same path
- preserve the existing fallback behavior

## Out Of Scope

- TTS or ASR
- Isaac Sim
- native Android app work
- Orin NX deployment work
- content-library redesign
- prompt-system overhaul
- broad refactors across core, adapters, services, and UI

## Architecture Constraints

- keep `core` platform-agnostic
- keep runtime-specific behavior in `services` or adapters
- `Narrator` abstraction must remain runtime-agnostic
- orchestrator must not depend directly on Ollama
- do one coherent bundle only

## Acceptance Criteria

- Ollama runtime is reachable from the repo's configured path
- configured model is available to the runtime
- gateway health clearly reports backend/model availability
- at least one narration request returns real model output
- at least one follow-up question returns real model output
- API and/or `/debug` can demonstrate the same path
- fallback behavior still exists if the runtime is unavailable

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers or risks

If you cannot fully close the round, stop at the narrowest real blocker and write that blocker clearly instead of expanding scope.
