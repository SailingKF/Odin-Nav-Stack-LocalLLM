# Current Round Result

## Round
Round 027 - Deployment Endpoint Config Canonicalization Baseline

## Summary

- Status: PASSED
- The repository now contains an explicit endpoint-config canonicalization layer underneath the deployment endpoint contract.
- Repo-owned service targets now follow one clear precedence story:
  1. canonical endpoint config
  2. legacy compatibility field
  3. default
- Existing command, verification, and result-summary layers remain aligned because they still consume the same endpoint contract.
- Example configs now demonstrate the preferred endpoint config shape directly.

## What I Changed

- Added a focused endpoint-config canonicalization module in:
  - `services/deployment_profile/endpoint_config.py`
- Updated the endpoint contract to build on top of the canonicalization seam:
  - `services/deployment_profile/endpoint_contract.py`
- Exported the canonicalization builder through:
  - `services/deployment_profile/__init__.py`
- Updated example configs to demonstrate the preferred explicit endpoint shape:
  - `configs/dev.yaml`
  - `configs/sim.yaml`
  - `configs/edge.yaml`
- Added focused canonicalization docs:
  - `docs/DEPLOYMENT_ENDPOINT_CONFIG_CANONICALIZATION.md`
- Updated endpoint and deployment docs:
  - `README.md`
  - `docs/DEPLOYMENT.md`
  - `docs/DEPLOYMENT_ENDPOINT_CONTRACT.md`
- Updated focused tests:
  - `tests/test_deployment_endpoint_contract.py`

## Exact Files Changed

- `README.md`
- `configs/dev.yaml`
- `configs/sim.yaml`
- `configs/edge.yaml`
- `docs/DEPLOYMENT.md`
- `docs/DEPLOYMENT_ENDPOINT_CONTRACT.md`
- `docs/DEPLOYMENT_ENDPOINT_CONFIG_CANONICALIZATION.md`
- `services/deployment_profile/__init__.py`
- `services/deployment_profile/endpoint_contract.py`
- `services/deployment_profile/endpoint_config.py`
- `tests/test_deployment_endpoint_contract.py`
- `coordination/latest_result.md` updated locally after commit only, not staged

## What Canonical Endpoint-Config Behavior I Introduced

New canonicalization seam:

- `build_canonical_endpoint_config(...)`

Current preferred config shape:

- `service_endpoints.<service_id>`

Current service ids covered:

- `llm_gateway`
- `api_server`
- `sim_pose_ingress_server`

The canonicalization layer now resolves endpoint values before the endpoint contract is built, so the rest of the repo does not need to know precedence details.

Current source labels are now:

- `canonical_endpoint_config`
- `legacy_compatibility`
- `default`

Current endpoint-contract output now includes:

- `preferred_config_shape`
- `canonical_config_path`
- `legacy_compatibility_fields`

alongside the existing:

- `bind_host`
- `connect_host`
- `port`
- `scheme`
- `base_url`
- per-field source markers

## What The Preferred Service Endpoint Config Shape Is Now

Current preferred explicit shape is:

```yaml
service_endpoints:
  llm_gateway:
    bind_host: 0.0.0.0
    connect_host: 127.0.0.1
    port: 9000
    scheme: http
  api_server:
    bind_host: 0.0.0.0
    connect_host: 127.0.0.1
    port: 8000
    scheme: http
```

This is now demonstrated directly in:

- `configs/dev.yaml`
- `configs/edge.yaml`
- `configs/sim.yaml`

The intent is:

- one explicit config shape for repo-owned service targets
- service-specific overrides without scattering host/port assumptions
- backward compatibility while the repo transitions away from older one-off fields

## How Legacy Fields Such As `llm_gateway_url` Are Handled

Current backward compatibility remains for:

- `llm_gateway_url`

When present on its own, `llm_gateway_url` still provides:

- `connect_host`
- `port`
- `scheme`
- `base_url`

It is now marked explicitly as:

- `legacy_compatibility`

This means the repo still preserves existing flows that rely on `llm_gateway_url`, including:

- narrator/client targeting
- verification target derivation
- runner target execution

but no longer treats that field as the preferred long-term endpoint config shape.

## What Precedence Rules Now Apply

Current precedence is:

1. `service_endpoints.<service_id>.*`
   - source label:
     - `canonical_endpoint_config`
2. legacy compatibility field, where supported
   - currently:
     - `llm_gateway_url`
   - source label:
     - `legacy_compatibility`
3. built-in default
   - source label:
     - `default`

For `llm_gateway`, this means:

- if both `service_endpoints.llm_gateway.port` and `llm_gateway_url` exist
  - the canonical endpoint config wins
- if only `llm_gateway_url` exists
  - the legacy field is still honored
- if neither exists
  - defaults are used

This is the main behavior change from Round 027:

- precedence is now explicit, centralized, and test-covered
- command/verification layers no longer need to infer precedence on their own

## How Operators Can Inspect Or Understand The Canonicalized Endpoint Contract Now

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

This output now makes explicit:

- the preferred config shape
- which values came from canonical endpoint config
- which values came from legacy compatibility
- which values still fell back to defaults

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_deployment_endpoint_contract -v`
  - passed
  - `Ran 4 tests ... OK`
- `python -m unittest tests.test_deployment_command_manifest -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_deployment_verification_manifest -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest tests.test_api_server -v`
  - passed
  - `Ran 6 tests ... OK`
- `python -m unittest tests.test_deployment_verification_runner -v`
  - passed
  - `Ran 4 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 91 tests ... OK`

Focused coverage now includes:

- legacy compatibility path for `llm_gateway_url`
- canonical endpoint config path for `service_endpoints.<service_id>`
- precedence when both canonical and legacy values are present
- verification-target alignment after canonicalization

### Manual

Ran:

- `python scripts/print_endpoint_contract.py --config configs/edge.yaml`

Confirmed current `edge.yaml` output:

- top-level:
  - `preferred_config_shape: "service_endpoints.<service_id>"`
- `llm_gateway`
  - `base_url: http://127.0.0.1:9000`
  - `bind_host_source: "canonical_endpoint_config"`
  - `connect_host_source: "canonical_endpoint_config"`
  - `port_source: "canonical_endpoint_config"`
  - `legacy_compatibility_fields: ["llm_gateway_url"]`
- `api_server`
  - `base_url: http://127.0.0.1:8000`
  - all endpoint fields currently come from:
    - `canonical_endpoint_config`

This confirms the repo can now answer:

- what the preferred endpoint config shape is
- when the repo is still using legacy compatibility
- when a config has already been canonicalized

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 28]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `c5f5cb9747feae58b0b7c232a7515074d03a080b`

## Staged / Committed State

- Round 027 code bundle: committed
- `coordination/latest_result.md`: updated locally after commit, not staged
- Unrelated local modification in `docs/DEV_WORKFLOW.md` remains untouched
- `coordination/` remains outside this commit, per handoff rule

## Blockers, Risks, Or Remaining Gaps Before Real Orin NX Or Hardware-Backed Deployment

- Canonicalization is currently focused only on repo-owned service endpoints, not general config normalization.
- Backward compatibility still exists for:
  - `llm_gateway_url`
  so the repo still carries a mixed-config story until a future cleanup round removes the legacy field.
- `api_server` and `sim_pose_ingress_server` do not currently have legacy fields, only canonical config plus defaults.
- The endpoint contract is still static/config-driven, not dynamic service discovery.
- This round intentionally stops at the narrow seam: one reusable canonical endpoint-config story with explicit precedence, without broadening into wider config-framework refactors or service-discovery behavior.
