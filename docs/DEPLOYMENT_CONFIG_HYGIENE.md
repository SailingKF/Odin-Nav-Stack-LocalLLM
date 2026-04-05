# Deployment Config Hygiene

## Purpose

This document defines the narrow endpoint-focused config-hygiene summary layer added on top of:

- endpoint config canonicalization
- endpoint contract
- deployment command / verification surfaces

The goal is to give operators one explicit answer to:

- whether a profile is already canonicalized
- whether legacy compatibility is still actively in use
- whether defaults are still carrying too much of the endpoint shape
- what migration step is recommended next

This round does not remove backward compatibility. It only makes the current migration state explicit.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/config_hygiene.py`

Operator-facing inspection entry point:

- `scripts/print_config_hygiene.py`

Runtime-facing exposure:

- `deployment_config_hygiene`

## Current Top-Level Surface

The config-hygiene summary exposes:

- `profile_name`
- `preferred_config_shape`
- `overall_hygiene_status`
- `legacy_compatibility_present`
- `legacy_compatibility_in_use`
- `deprecation_cleanup_needed`
- `legacy_compatibility_fields_present`
- `legacy_compatibility_fields_in_use`
- per-status service counts
- `services`
- `recommended_actions`

## Service-Level Statuses

Each repo-owned service currently lands in one of these statuses:

- `fully_canonicalized`
  - all tracked endpoint fields come from `service_endpoints.<service_id>`
- `partially_canonicalized`
  - at least one field is canonical, but some fields still come from defaults
- `mixed_canonical_and_legacy`
  - one service currently mixes canonical endpoint values with legacy compatibility values
- `legacy_dependent`
  - the service still depends on legacy compatibility fields
- `default_heavy`
  - the service is still driven entirely by built-in defaults

## Overall Hygiene Statuses

The top-level `overall_hygiene_status` currently uses:

- `fully_canonicalized`
- `partially_canonicalized`
- `mixed_canonical_and_legacy`
- `legacy_dependent`
- `default_heavy`
- `no_repo_owned_service_endpoints`

## How Legacy Compatibility Is Reported

Legacy compatibility is reported in two separate ways:

- `legacy_compatibility_present`
  - a deprecated compatibility field such as `llm_gateway_url` still exists in config
- `legacy_compatibility_in_use`
  - endpoint resolution still actively depends on a legacy compatibility value

This distinction matters because a profile can already be canonicalized while still carrying an unused legacy field that should be removed later.

## Recommended Migration Guidance

Recommended actions are generated per service and also aggregated at the top level.

Current migration guidance follows these rules:

- `default_heavy`
  - add a full `service_endpoints.<service_id>` block
- `partially_canonicalized`
  - fill in the remaining canonical fields so defaults stop carrying endpoint behavior
- `mixed_canonical_and_legacy`
  - complete the canonical block so one service is not resolved from two config styles at once
- `legacy_dependent`
  - add canonical endpoint config first, then retire the legacy field
- `fully_canonicalized` with deprecated fields still present
  - remove the unused legacy field after confirming the canonical endpoint is the intended long-term target

## How To Inspect It

Use:

```text
python scripts/print_config_hygiene.py --config configs/dev.yaml
python scripts/print_config_hygiene.py --config configs/sim.yaml
python scripts/print_config_hygiene.py --config configs/edge.yaml
```

Or inspect:

- API `health`
- API `state`
- sim ingress `health`
- sim ingress `state`

## What This Layer Does Not Do

This layer does not:

- remove backward compatibility
- rewrite config files automatically
- validate unrelated non-endpoint settings
- perform startup automation
- replace deployment packaging or service supervision

It only summarizes:

- endpoint config hygiene
- deprecation visibility
- migration intent
