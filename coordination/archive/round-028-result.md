# Current Round Result

## Round
Round 028 - Deployment Config Hygiene And Deprecation Summary Baseline

## Summary

- Status: PASSED
- The repository now contains an explicit endpoint-focused config-hygiene summary layer on top of endpoint canonicalization and the endpoint contract.
- Operators can now see, without reading code:
  - whether a profile is fully canonicalized, partially canonicalized, mixed, legacy-dependent, or default-heavy
  - whether deprecated compatibility fields are merely present or still actively in use
  - what migration action is recommended next
- Backward compatibility remains intact. This round only surfaced hygiene/deprecation state and migration guidance.

## What I Changed

- Added a focused config-hygiene module in:
  - `services/deployment_profile/config_hygiene.py`
- Exported the hygiene builder through:
  - `services/deployment_profile/__init__.py`
- Exposed the new hygiene summary in runtime surfaces:
  - `services/api_server/runtime.py`
  - `services/sim_pose_ingress/runtime.py`
- Added an operator-facing inspection script:
  - `scripts/print_config_hygiene.py`
- Added focused docs:
  - `docs/DEPLOYMENT_CONFIG_HYGIENE.md`
- Updated deployment/operator docs:
  - `README.md`
  - `docs/DEPLOYMENT.md`
  - `docs/DEPLOYMENT_ENDPOINT_CONTRACT.md`
- Added focused tests and runtime assertions:
  - `tests/test_deployment_config_hygiene.py`
  - `tests/test_api_server.py`

## Exact Files Changed

- `README.md`
- `docs/DEPLOYMENT.md`
- `docs/DEPLOYMENT_ENDPOINT_CONTRACT.md`
- `docs/DEPLOYMENT_CONFIG_HYGIENE.md`
- `scripts/print_config_hygiene.py`
- `services/deployment_profile/__init__.py`
- `services/deployment_profile/config_hygiene.py`
- `services/api_server/runtime.py`
- `services/sim_pose_ingress/runtime.py`
- `tests/test_api_server.py`
- `tests/test_deployment_config_hygiene.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## What Config-Hygiene / Deprecation Surface I Introduced

New reusable builder:

- `build_deployment_config_hygiene(config, deployment_endpoint_contract)`

New runtime-visible surface:

- `deployment_config_hygiene`

New operator-facing script:

- `python scripts/print_config_hygiene.py --config configs/<profile>.yaml`

The hygiene surface is machine-readable and intentionally narrow. It only summarizes endpoint-related config state for repo-owned services already covered by the endpoint contract.

## What Hygiene Statuses Now Exist

### Overall statuses

- `fully_canonicalized`
- `partially_canonicalized`
- `mixed_canonical_and_legacy`
- `legacy_dependent`
- `default_heavy`
- `no_repo_owned_service_endpoints`

### Service-level statuses

- `fully_canonicalized`
  - all tracked endpoint fields come from `service_endpoints.<service_id>`
- `partially_canonicalized`
  - canonical config exists, but some endpoint fields still come from defaults
- `mixed_canonical_and_legacy`
  - one service resolves endpoint values from both canonical config and legacy compatibility
- `legacy_dependent`
  - the service still depends on legacy compatibility fields
- `default_heavy`
  - the service is still entirely default-derived

## How Legacy Compatibility Usage Is Reported Now

The summary now distinguishes between:

- `legacy_compatibility_present`
  - deprecated compatibility fields still exist in config
- `legacy_compatibility_in_use`
  - endpoint resolution still actively depends on legacy compatibility

It also exposes:

- `legacy_compatibility_fields_present`
- `legacy_compatibility_fields_in_use`

At the service level it additionally shows:

- `legacy_compatibility_fields_supported`
- `legacy_compatibility_fields_present`
- `legacy_fields_in_use`

This means a profile can now be reported as:

- fully canonicalized
  - while still carrying an unused deprecated field that should be cleaned up later

which was not explicit before this round.

## What Recommended Migration Actions Are Surfaced

Per-service and aggregated top-level actions now cover:

- `default_heavy`
  - add an explicit `service_endpoints.<service_id>` block
- `partially_canonicalized`
  - fill in the remaining canonical fields so defaults stop carrying behavior
- `mixed_canonical_and_legacy`
  - complete the canonical block so one service is not resolved from two config styles
- `legacy_dependent`
  - add canonical endpoint config first, then retire the legacy field
- `fully_canonicalized` with deprecated fields still present
  - remove the unused legacy field after confirming canonical parity

## How Operators Can Inspect The Hygiene Summary Now

### Script

```text
python scripts/print_config_hygiene.py --config configs/dev.yaml
python scripts/print_config_hygiene.py --config configs/sim.yaml
python scripts/print_config_hygiene.py --config configs/edge.yaml
```

### Runtime surfaces

- API `health`
- API `state`
- sim ingress `health`
- sim ingress `state`

Look for:

- `deployment_config_hygiene.overall_hygiene_status`
- `deployment_config_hygiene.legacy_compatibility_present`
- `deployment_config_hygiene.legacy_compatibility_in_use`
- `deployment_config_hygiene.services`
- `deployment_config_hygiene.recommended_actions`

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_deployment_config_hygiene -v`
  - passed
  - `Ran 4 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 95 tests ... OK`

Focused coverage now includes:

- fully canonicalized config
- legacy-only config
- mixed canonical-plus-legacy config
- default-heavy config
- partially canonicalized config
- recommended-action generation
- runtime exposure through API state/health

### Manual

Ran:

- `python scripts/print_config_hygiene.py --config configs/dev.yaml`
- `python scripts/print_config_hygiene.py --config configs/sim.yaml`

Confirmed current `dev.yaml` output:

- `overall_hygiene_status: "fully_canonicalized"`
- `legacy_compatibility_present: true`
- `legacy_compatibility_in_use: false`
- `recommended_actions` includes removal guidance for:
  - `llm_gateway_url`

Confirmed current `sim.yaml` output:

- `overall_hygiene_status: "fully_canonicalized"`
- both repo-owned services currently resolve from:
  - `canonical_endpoint_config`
- `llm_gateway_url` remains present but is not used by active repo-owned service endpoint resolution in this launch shape

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 29]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `a33723c54ad67675b903616e3258105e27bf2d09`

## Staged / Committed State

- Round 028 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule

## Blockers, Risks, Or Remaining Gaps Before Real Orin NX Or Hardware-Backed Deployment

- This hygiene layer is intentionally endpoint-focused only. It does not broaden into general config linting.
- Backward compatibility is still preserved for:
  - `llm_gateway_url`
  so the repo still supports old shapes while surfacing deprecation/migration guidance.
- The current summary is config-derived, not runtime-discovered. It does not prove a target is reachable.
- The runtime surfaces now tell operators how clean the config is, but not when to enforce removal. A future round would need to define the actual deprecation cutover policy.
- This round intentionally stops before packaging, service discovery, automatic startup, or wider schema refactors.
