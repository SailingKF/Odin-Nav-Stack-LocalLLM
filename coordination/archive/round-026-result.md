# Current Round Result

## Round
Round 026 - Deployment Endpoint Contract And Config-Driven Target Baseline

## Summary

- Status: PASSED
- The repository now contains an explicit deployment endpoint-contract layer for repo-owned internal services.
- Repo-owned service targets now derive from one reusable source instead of being hard-coded separately in command and verification layers.
- Existing runtime/API surfaces now expose `deployment_endpoint_contract`.
- Command manifest, verification manifest, and verification runner are now aligned around the same host/port/base-url contract.

## What I Changed

- Added a focused endpoint-contract module in:
  - `services/deployment_profile/endpoint_contract.py`
- Exported it through:
  - `services/deployment_profile/__init__.py`
- Wired endpoint-contract exposure into runtime-facing services:
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
- Updated the command-manifest layer to derive repo command host/port args from the endpoint contract:
  - `services/deployment_profile/command_manifest.py`
- Updated the verification-manifest layer to derive target URLs from the endpoint contract:
  - `services/deployment_profile/verification_manifest.py`
- Updated operator-facing scripts to reuse the endpoint contract:
  - `scripts/print_bringup_sheet.py`
  - `scripts/print_verification_sheet.py`
  - `scripts/run_verification_summary.py`
- Added an operator-facing endpoint inspection script:
  - `scripts/print_endpoint_contract.py`
- Added focused endpoint-contract tests in:
  - `tests/test_deployment_endpoint_contract.py`
- Updated existing deployment tests so command/verification alignment is validated through the new contract:
  - `tests/test_deployment_command_manifest.py`
  - `tests/test_deployment_verification_manifest.py`
  - `tests/test_deployment_verification_runner.py`
  - `tests/test_api_server.py`
- Updated docs:
  - `README.md`
  - `docs/DEPLOYMENT.md`
  - `docs/DEPLOYMENT_COMMAND_MANIFEST_CONTRACT.md`
  - `docs/DEPLOYMENT_VERIFICATION_MANIFEST_CONTRACT.md`
  - `docs/DEPLOYMENT_ENDPOINT_CONTRACT.md`

## Exact Files Changed

- `README.md`
- `docs/DEPLOYMENT.md`
- `docs/DEPLOYMENT_COMMAND_MANIFEST_CONTRACT.md`
- `docs/DEPLOYMENT_VERIFICATION_MANIFEST_CONTRACT.md`
- `docs/DEPLOYMENT_ENDPOINT_CONTRACT.md`
- `scripts/print_bringup_sheet.py`
- `scripts/print_verification_sheet.py`
- `scripts/run_verification_summary.py`
- `scripts/print_endpoint_contract.py`
- `services/api_server/runtime.py`
- `services/deployment_profile/__init__.py`
- `services/deployment_profile/command_manifest.py`
- `services/deployment_profile/verification_manifest.py`
- `services/deployment_profile/endpoint_contract.py`
- `services/sim_pose_ingress/runtime.py`
- `tests/test_api_server.py`
- `tests/test_deployment_command_manifest.py`
- `tests/test_deployment_verification_manifest.py`
- `tests/test_deployment_verification_runner.py`
- `tests/test_deployment_endpoint_contract.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## What Endpoint-Contract Surface I Introduced

New runtime-visible surface:

- `deployment_endpoint_contract`

Current top-level fields:

- `profile_name`
- `services`
- `service_count`

Each service entry currently exposes:

- `service_id`
- `step_id`
- `profile_name`
- `bind_host`
- `connect_host`
- `port`
- `scheme`
- `base_url`
- `bind_host_source`
- `connect_host_source`
- `port_source`
- `scheme_source`
- `base_url_source`

Current repo-owned services covered:

- `llm_gateway`
- `api_server`
- `sim_pose_ingress_server`

## How Repo-Owned Service Targets Are Now Derived From Config/Defaults

The current endpoint contract derives service targets from one clear place:

- `services/deployment_profile/endpoint_contract.py`

Current derivation rules:

### `llm_gateway`

- `connect_host`, `port`, and `base_url`
  - derive from `llm_gateway_url` when configured
- `bind_host`
  - defaults to `0.0.0.0`
  - can be overridden with:
    - `service_endpoints.llm_gateway.bind_host`

This keeps:

- narrator/client-facing target
- command-manifest port
- verification-manifest target URL

aligned around the same configured gateway URL.

### `api_server`

Current defaults:

- `bind_host: 0.0.0.0`
- `connect_host: 127.0.0.1`
- `port: 8000`
- `base_url: http://127.0.0.1:8000`

Optional config overrides:

- `service_endpoints.api_server.bind_host`
- `service_endpoints.api_server.connect_host`
- `service_endpoints.api_server.port`
- `service_endpoints.api_server.scheme`

### `sim_pose_ingress_server`

Current defaults:

- `bind_host: 127.0.0.1`
- `connect_host: 127.0.0.1`
- `port: 8100`
- `base_url: http://127.0.0.1:8100`

Optional config overrides:

- `service_endpoints.sim_pose_ingress_server.bind_host`
- `service_endpoints.sim_pose_ingress_server.connect_host`
- `service_endpoints.sim_pose_ingress_server.port`
- `service_endpoints.sim_pose_ingress_server.scheme`

## Which Targets Remain Defaulted Vs Explicitly Configured

Current actual `dev.yaml` endpoint output:

- `llm_gateway`
  - `base_url: http://127.0.0.1:9000`
  - `connect_host_source: config-driven`
  - `port_source: config-driven`
  - `scheme_source: config-driven`
  - because `llm_gateway_url` is configured
- `api_server`
  - `base_url: http://127.0.0.1:8000`
  - `bind_host_source: defaulted`
  - `connect_host_source: defaulted`
  - `port_source: defaulted`
  - because no `service_endpoints.api_server` override exists yet

Current actual `sim` override behavior is now supported and covered by tests:

- `sim_pose_ingress_server`
  - can derive `bind_host`, `connect_host`, and `port` from `service_endpoints.sim_pose_ingress_server`
  - otherwise stays on default `127.0.0.1:8100`

This is the key drift fix from Round 026:

- command argv and verification target URLs no longer own separate hard-coded host/port assumptions
- both now reuse the endpoint contract

## How Operators Can Inspect The Endpoint Contract Now

### API Surfaces

Operators can inspect:

- `deployment_endpoint_contract`

through:

- API `health`
- API `state`
- sim ingress runtime `health`
- sim ingress runtime `state`

### Script Entry Point

Operators can now run:

```text
python scripts/print_endpoint_contract.py --config configs/dev.yaml
python scripts/print_endpoint_contract.py --config configs/sim.yaml
python scripts/print_endpoint_contract.py --config configs/edge.yaml
```

The output makes these points explicit in one place:

- bind host
- connect host
- port
- base URL
- whether each value came from config or defaults

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_deployment_endpoint_contract -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_deployment_command_manifest -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_deployment_verification_manifest -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 90 tests ... OK`

Focused coverage now includes:

- endpoint derivation for `dev`
- config override behavior for `sim`
- verification-target alignment with derived endpoint contract
- runtime/API exposure of `deployment_endpoint_contract`
- command-manifest argv alignment with endpoint contract

### Manual

Ran:

- `python scripts/print_endpoint_contract.py --config configs/dev.yaml`

Confirmed:

- `llm_gateway` now reports:
  - `base_url: http://127.0.0.1:9000`
  - `bind_host_source: defaulted`
  - `connect_host_source: config-driven`
  - `port_source: config-driven`
- `api_server` now reports:
  - `base_url: http://127.0.0.1:8000`
  - all source flags currently `defaulted`

This shows the repo can now answer:

- what local endpoint each repo-owned service assumes
- which values are explicit config choices
- which values are still implicit defaults

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 27]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `2e26e7bc3d49dce25fa89e2f7ea0363f20ec5f42`

## Staged / Committed State

- Round 026 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule

## Blockers, Risks, Or Remaining Gaps Before Real Orin NX Or Hardware-Backed Deployment

- The endpoint contract is still static/config-driven, not dynamic service discovery.
- It does not yet:
  - discover services automatically
  - reconcile multiple network interfaces
  - manage reverse proxies
  - package edge networking assumptions for Orin NX
- `api_server` and `sim_pose_ingress_server` still rely on defaults unless operators add `service_endpoints` overrides.
- `llm_gateway` still uses `llm_gateway_url` as the main configured client-facing source, so future config cleanup may want to converge all service targets under one explicit endpoint block.
- This round intentionally stops at the narrow seam: one reusable endpoint contract that removes target drift between command, verification, and result-summary layers, without broadening into service discovery or startup automation.
