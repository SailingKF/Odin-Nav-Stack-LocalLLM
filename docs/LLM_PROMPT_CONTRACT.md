# Local LLM Prompt Contract

## Purpose

This document defines the narrow contract between structured POI content and the local LLM prompt layer.

The goal is not to let the model invent a richer tour from open knowledge.
The goal is to let the model express repository-owned POI content in a slightly more natural guide voice while keeping the structured content package as the source of truth.

## Scope

This contract applies to:
- `services/llm_gateway/prompting.py`
- `services/llm_gateway/backends.py`
- `core/narrator/local_llm_narrator.py`
- the structured POI files under `content/poi/`

It does not change:
- `core` abstractions
- orchestrator state handling
- session schema
- Android debug page structure

## Source Of Truth Hierarchy

For one POI, the model should ground itself in this order:

1. mode-specific base text
   - `short_text`
   - `standard_text`
   - `extended_text`
2. `faq`
3. `facts`
4. optional framing fields
   - `tags`
   - `persona`
   - `theme`

The model should not rely on outside world knowledge when answering tour narration or follow-up questions for the current POI.

## Narration Contract

### Short

- intended for quick glance or phone-sized status
- one sentence
- should primarily restate `short_text`
- may add at most one small supporting fact if it still reads naturally

### Standard

- intended as the default guided explanation
- two sentences
- should primarily restate `standard_text`
- may blend in one supporting fact if it improves clarity

### Extended

- intended for a richer but still bounded on-site explanation
- three or four sentences
- should primarily restate `extended_text`
- may blend in up to two supporting facts

## Follow-Up Q&A Contract

For `answer_question(spot, question)`:

1. prefer the closest relevant FAQ answer
2. otherwise answer from `facts` and the authoritative base texts
3. if the requested detail is not supported by the POI package, return:

`The current POI content does not include that detail.`

This explicit fallback is intentional.
It is better to decline unsupported details than to let the local model improvise.

## Prompting Rules

- prompts must tell the model that the supplied POI content package is the only source of truth
- prompts must explicitly forbid invention and unsupported extrapolation
- prompts must define a clear answer shape for each narration mode
- prompts should return plain text only, with no labels or bullet lists
- model-specific transport details belong in gateway adapters, not in `core`

## Content Authoring Guidance

When adding or revising a POI:

- `short_text` should stand alone as a clean one-line intro
- `standard_text` should be the baseline explanation
- `extended_text` should add context, not random length
- `facts` should hold concise supportable points
- `faq` should cover the most likely operator or visitor follow-up questions

If the content package is weak, prompt tuning alone will not rescue output quality.

## Evaluation Guidance

When checking real local-LLM behavior:

- compare `short`, `standard`, and `extended` on the same POI
- check that the answer stays close to the content package
- ask one supported question and one unsupported question
- verify the unsupported question is declined cleanly rather than hallucinated

## Current Baseline Runtime

Current development baseline:
- backend: `ollama`
- model: `gemma3:4b`
- fallback: enabled

This is a development validation baseline, not a permanent runtime lock-in.
