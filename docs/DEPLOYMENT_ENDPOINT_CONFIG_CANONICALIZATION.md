# Deployment Endpoint Config Canonicalization

## Purpose

This document defines the narrow endpoint-config canonicalization layer that sits underneath:

- `deployment_endpoint_contract`

The goal is to make repo-owned endpoint derivation follow one preferred config shape while preserving backward compatibility for older fields such as `llm_gateway_url`.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/endpoint_config.py`

Current preferred config shape:

- `service_endpoints.<service_id>`

## Preferred Config Shape

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

Current service ids supported:

- `llm_gateway`
- `api_server`
- `sim_pose_ingress_server`

## Backward Compatibility

Current legacy compatibility support remains for:

- `llm_gateway_url`

When present on its own, `llm_gateway_url` still provides:

- `connect_host`
- `port`
- `scheme`
- `base_url`

`bind_host` remains on defaults unless the canonical shape overrides it.

## Current Precedence Rules

Current precedence is:

1. `service_endpoints.<service_id>.*`
   - source label:
     - `canonical_endpoint_config`
2. legacy compatibility field, where supported
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

## How This Appears In The Endpoint Contract

Current endpoint entries now report:

- `bind_host_source`
- `connect_host_source`
- `port_source`
- `scheme_source`
- `base_url_source`

Current source values are:

- `canonical_endpoint_config`
- `legacy_compatibility`
- `default`

This makes precedence visible to operators and reviewers instead of leaving it implicit in code paths.

## Why This Exists

Without canonicalization, endpoint derivation would continue to mix:

- historical fields
- newer service-specific overrides
- built-in defaults

That would keep command manifest, verification manifest, and result summaries vulnerable to drift.

This layer prevents that by centralizing endpoint precedence knowledge in one reusable place.
