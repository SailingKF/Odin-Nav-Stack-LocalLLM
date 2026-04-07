# Current Round Result

## Round
Round 002 - Content And Prompt Convergence Baseline

## Summary

- Status: PASSED
- The local-LLM path still works on the development machine with `gemma3:4b`.
- Prompt construction is now more explicit about mode shape, grounding, FAQ priority, and unsupported-detail refusal.
- Real sample outputs were captured from the live Ollama-backed gateway after the prompt changes.

## What Changed

- Tightened `services/llm_gateway/prompting.py` so narration modes are more clearly separated:
  - `short` now asks for exactly 1 sentence and prioritizes `short_text`
  - `standard` now asks for 2 sentences and prioritizes `standard_text`
  - `extended` now asks for 3 or 4 sentences and prioritizes `extended_text`
- Added stronger grounding rules so the model stays inside the supplied POI content package.
- Tightened follow-up Q&A prompting to:
  - prefer FAQ first
  - use facts/base texts second
  - refuse unsupported detail with the exact fallback sentence
  - avoid substituting nearby but incorrect facts
- Improved demo POI copy in `content/poi/demo_pois.yaml` so the three narration modes have clearer source material.
- Added a focused contract doc for the prompt/content boundary.
- Added non-brittle prompt-construction tests.
- Confirmed the real `gemma3:4b` development path still works after the prompt changes.

## Exact Files Changed

- `README.md`
- `content/poi/demo_pois.yaml`
- `services/llm_gateway/prompting.py`
- `docs/LLM_PROMPT_CONTRACT.md`
- `tests/test_prompting.py`
- `coordination/latest_result.md`

## Validation Performed

### Automated

- `python -m unittest discover -s tests`
  - passed
  - `Ran 19 tests ... OK`

### Runtime Regression

- Started the live gateway with:
  - `python scripts/run_llm_gateway.py --config configs/dev.yaml`
- Ran:
  - `python scripts/run_mock_tour.py`
- Result:
  - local narrator path still works
  - narration remained grounded to POI content
  - mock tour completed successfully with live local-LLM-backed narration

### Real Gemma Samples

Backend in use for all samples:
- `ollama`
- model: `gemma3:4b`
- fallback used: `false`

POI used for comparison:
- `Central Plaza`

#### Short

```text
This is the Central Plaza, the mid-route checkpoint in the demo tour.
```

#### Standard

```text
This is the Central Plaza, the mid-route checkpoint in the demo tour. Its position helps us verify mid-route trigger behavior and confirms narration continues correctly after the first POI.
```

#### Extended

```text
This is the Central Plaza, and it鈥檚 our second stop on the demo route. As a mid-route checkpoint, it鈥檚 crucial for verifying that the tour continues smoothly after the initial stop. We鈥檙e checking route progress, trigger stability, and ensuring that narration continues correctly.
```

#### Supported Follow-Up Question

Question:

```text
Why is the plaza important?
```

Answer:

```text
It gives us a mid-route stop to confirm the tour can continue after the first narration event.
```

#### Unsupported Follow-Up Question

Question:

```text
Which year was this plaza built?
```

Answer:

```text
The current POI content does not include that detail.
```

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 3]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `11330811ad23805768c2c76fe333ffe24ba45d20`

## Staged / Committed State

- Work for this round: committed
- Latest result handoff file: updated locally, not staged
- Unrelated local change remains in `docs/DEV_WORKFLOW.md` and was not touched in this round

## Blockers, Risks, Or Remaining Quality Issues

- `gemma3:4b` now follows the unsupported-detail fallback correctly for the tested case, but output style can still stay close to base text when the content package is intentionally narrow.
- The model is now better differentiated across `short`, `standard`, and `extended`, but further stylistic tuning would still be possible later if we want more expressive spread without breaking grounding.
- The worktree still contains an unrelated modification in `docs/DEV_WORKFLOW.md`; it was intentionally left alone.
- The `coordination/` directory is still untracked in git.
