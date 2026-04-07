# Current Round Prompt

## Round
Round 002 - Content And Prompt Convergence Baseline

## Goal
Now that the real local Gemma path works on the development machine, improve output control and quality consistency for narration and follow-up Q&A without widening system scope.

## Why This Is The Current Priority

The local runtime path is no longer the main risk.
The next main risk is output quality drift:
- mode differences may be weak
- answers may be too generic
- unsupported questions need clearer grounded behavior
- the project still needs to prove that structured content stays the source of truth

This round should make the real local-LLM behavior more controlled and easier to evaluate.

## In Scope

- refine `services/llm_gateway/prompting.py` so narration and Q&A are more tightly grounded in structured POI content
- make `short`, `standard`, and `extended` mode expectations clearer and more distinct
- improve follow-up Q&A prompting so FAQ/facts are prioritized and unsupported-detail responses are explicit
- make small, targeted improvements to demo POI structured content if needed to better support the three narration modes and follow-up answers
- add or update tests for prompt construction and related non-regression paths
- add one focused doc describing the local-LLM prompt/content contract for this project
- manually validate a few real `gemma3:4b` examples and record them in the result

## Out Of Scope

- TTS or ASR
- Isaac Sim
- native Android app work
- Orin NX deployment work
- RAG, vector database, or retrieval-system work
- broad narrator-interface redesign
- major session-logging refactor
- frontend redesign
- multi-POI conversation memory

## Architecture Constraints

- structured content remains the source of truth
- do not move model-specific logic into `core`
- keep orchestrator and narrator abstractions runtime-agnostic
- keep changes concentrated in content, gateway prompting, tests, and focused docs
- do one coherent bundle only

## Acceptance Criteria

- prompt construction clearly differentiates `short`, `standard`, and `extended`
- prompt construction clearly constrains the model to supplied POI content
- follow-up Q&A prompt clearly prefers FAQ/facts and declines unsupported details cleanly
- tests cover the updated prompt behavior without asserting brittle exact LLM wording
- existing test suite still passes
- the repository still works with the current real local-LLM dev setup
- the result includes real `gemma3:4b` sample outputs for:
  - one POI in `short`
  - the same POI in `standard`
  - the same POI in `extended`
  - one supported follow-up question
  - one unsupported follow-up question

## Result Requirements

When done, update `coordination/latest_result.md` with:
- what you changed
- exact files changed
- exact validation performed
- the real sample outputs requested above
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining quality issues

If you hit a blocker, do not widen scope.
Stop at the narrowest real blocker and describe it clearly.
