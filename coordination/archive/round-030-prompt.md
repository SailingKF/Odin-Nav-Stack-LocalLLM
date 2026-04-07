# Current Round Prompt

## Round
Round 030 - MVSim Guided Validation Harness Baseline

## Goal
Add a narrow operator-facing validation harness so a human can open one program/page and manually inspect whether the MVSim PC validation path is healthy, instead of manually coordinating multiple terminals and ad hoc API calls.

## Why This Is The Current Priority

Round 029 proved that the MVSim-oriented compatibility path works, but the current validation flow is still too engineer-heavy:

- start sim ingress manually
- start API proxy manually
- run bridge demo manually
- inspect multiple endpoints manually

That is fine for development, but too awkward for quick human acceptance.

The next highest-value improvement is not more simulator depth. It is a simple validation experience that lets an operator or stakeholder quickly see:

- whether the required local services are up
- whether the tour ran
- whether POIs triggered
- whether the session completed
- whether `/debug` is available
- whether a follow-up question succeeds

This should stay a local PC validation tool, not become a general deployment supervisor.

## In Scope

- introduce a narrow MVSim validation harness for PC-only use
- make manual verification substantially easier than the current multi-terminal flow
- acceptable shapes include:
  - a lightweight local app/page
  - a local validation runner that opens or serves a human-readable report page
  - a small operator-facing launcher plus result summary UI
- the harness should surface the key checks a human actually cares about, including at minimum:
  - sim-ingress reachability
  - sim-profile API reachability
  - `/debug` availability
  - bridge/demo run status
  - route completion
  - latest POI / latest narration
  - latest session id
  - follow-up question result
- if the harness launches local child processes, keep it clearly local/dev-only and narrow in scope
- include clear handling or reporting for common operator problems such as:
  - required port already occupied
  - upstream service not reachable
  - bridge/demo run failed
- add focused docs explaining the easiest human-validation path
- add focused tests where practical for the harness/report logic

## Desired UX

The user should ideally be able to do one of these:

- run one command and then open one local page
- or run one command that opens a page automatically
- or run one narrow launcher and click a small number of obvious buttons

The end result should be that a non-programmer can visually inspect the result without manually chaining REST calls.

## Out Of Scope

- direct live MVSim runtime/process integration
- Isaac Sim
- ROS formal adapter
- map-format or occupancy-map design
- real hardware integration
- Orin NX packaging or service management
- long-running supervisor/process manager design
- general deployment orchestration
- real TTS engine work
- ASR

## Architecture Constraints

- keep `core` platform-agnostic
- keep this as an operator-validation seam, not a production runtime redesign
- reuse the current sim-ingress, API proxy, and MVSim bridge surfaces
- do not turn this into a broad GUI framework migration
- do not introduce a general-purpose process supervisor
- preserve the current simulation contracts and existing `/debug` path
- keep the bundle coherent and narrow

## Acceptance Criteria

- repository contains a clear human-usable MVSim validation harness
- a user can validate the current MVSim PC path without manually performing multiple REST calls
- the harness clearly shows pass/fail or healthy/unhealthy state for key checks
- the harness gives the user an obvious path to open or inspect `/debug`
- focused tests pass
- existing related tests still pass
- docs clearly explain the easiest manual validation flow

## Result Requirements

When done, update `coordination/latest_result.md` with:

- what you changed
- exact files changed
- what the new validation harness is
- exactly how a human should use it
- whether it launches processes, attaches to existing ones, or supports both
- what checks/results are visible in the harness
- how port conflicts and missing upstreams are reported
- exact validation performed
- branch name
- full `git status --short --branch`
- commit hash
- whether files are staged and/or committed
- blockers, risks, or remaining gaps

If you hit a blocker, do not expand scope into simulator redesign, ROS formalization, or packaging.
Stop at the narrowest real blocker and describe it clearly.
