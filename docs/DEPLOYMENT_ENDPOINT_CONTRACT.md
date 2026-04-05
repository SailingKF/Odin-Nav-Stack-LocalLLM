# Deployment Endpoint Contract

## Purpose

This document defines the narrow endpoint-contract layer that sits alongside:

- deployment launch plan
- deployment command manifest
- deployment verification manifest

The goal is to keep repo-owned host/port/base-url assumptions in one reusable place so startup commands, verification checks, and result summaries stay aligned when ports or hosts change.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/endpoint_contract.py`

Operator-facing inspection entry point:

- `scripts/print_endpoint_contract.py`

Current runtime-facing exposure:

- `deployment_endpoint_contract`

## Current Top-Level Surface

The endpoint contract exposes:

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

## Current Repo-Owned Services Covered

- `llm_gateway`
- `api_server`
- `sim_pose_ingress_server`

These are derived only when the relevant internal-service steps exist in the active launch plan.

## Current Derivation Rules

### `llm_gateway`

Current behavior:

- `connect_host`, `port`, and `base_url` derive from `llm_gateway_url` when configured
- `bind_host` defaults to `0.0.0.0` unless explicitly overridden through:
  - `service_endpoints.llm_gateway.bind_host`

This keeps:

- narrator/client-facing target
- deployment verification target
- command-manifest port

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

## How Other Deployment Surfaces Reuse This Contract

Current reuse points:

- command manifest
  - command argv now include `--host` and `--port` from the endpoint contract
- verification manifest
  - verification target URLs now derive from `base_url`
- verification runner / summary
  - one-shot checks now inherit aligned targets through the verification manifest

## How To Inspect It

Use:

```text
python scripts/print_endpoint_contract.py --config configs/dev.yaml
python scripts/print_endpoint_contract.py --config configs/sim.yaml
python scripts/print_endpoint_contract.py --config configs/edge.yaml
```

Or inspect:

- API `health`
- API `state`
- sim ingress `health`
- sim ingress `state`

## What This Layer Does Not Automate

This layer does not yet:

- discover services dynamically
- start services
- manage networking/routing
- introduce service discovery
- replace deployment packaging

It only centralizes:

- repo-owned endpoint assumptions
- source-of-value visibility
- alignment between command, verification, and result-summary layers
