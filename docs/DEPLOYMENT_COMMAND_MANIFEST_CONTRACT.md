# Deployment Command Manifest Contract

## Purpose

This document defines the narrow command-manifest layer that sits on top of:

- deployment launch plan
- deployment readiness

The goal is to make repo-owned bring-up commands explicit without turning the repository into a launcher, process supervisor, or packaging system.

## Implementation Location

Current implementation lives in:

- `services/deployment_profile/command_manifest.py`

Operator-facing inspection entry point:

- `scripts/print_bringup_sheet.py`

Current runtime-facing exposure:

- `deployment_command_manifest`

Related post-start verification layer:

- `deployment_verification_manifest`

## Current Top-Level Surface

The command manifest exposes:

- `profile_name`
- `automation_level`
- `config_path`
- `commands`
- `steps`
- `command_count`
- `repo_command_step_count`
- `manual_step_count`

This means:

- repo-owned startup commands are available from one reusable place
- manual/external steps remain visible and explicit
- the repo still does not auto-run or supervise these commands

## Command Entry Shape

Each repo-owned command currently exposes:

- `command_id`
- `step_id`
- `order`
- `profile_name`
- `command_kind`
- `entrypoint_path`
- `argv`
- `display_command`
- `config_path`
- `description`
- `owned_by_repo`

Current command kind:

- `python_script`

## Step Mapping Shape

Each launch-plan step is also summarized in the manifest with:

- `step_id`
- `order`
- `name`
- `category`
- `required`
- `action_type`
- `command_available`
- `command_id`
- `operator_action`
- `detail`
- `startup_hint`

Current action types:

- `repo_command`
- `manual_external`
- `manual_optional`

## Current Repo-Owned Command Mapping

### dev

Repo-owned commands currently map:

- `llm_gateway`
  - `python scripts/run_llm_gateway.py --config configs/dev.yaml`
- `api_server`
  - `python scripts/run_api_server.py --config configs/dev.yaml`

Manual/non-command steps remain:

- `ollama_runtime`
- `debug_browser`

### sim

Repo-owned commands currently map:

- `sim_pose_ingress_server`
  - `python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml`
- `api_server`
  - `python scripts/run_api_server.py --config configs/sim.yaml`

Manual/non-command steps remain:

- `isaac_live_dependency`
- `isaac_stub_source`
- `sim_publisher_bridge`

The publisher bridge is intentionally still non-commanded here because this round does not turn demo bridge runners into a stable bring-up service contract.

### edge

Repo-owned commands currently map:

- `llm_gateway`
  - `python scripts/run_llm_gateway.py --config configs/edge.yaml`
- `api_server`
  - `python scripts/run_api_server.py --config configs/edge.yaml`

Manual/non-command steps remain:

- `hardware_pose_dependency`
- `ollama_runtime`
- `audio_device_dependency`

## Guided Bring-Up Sheet

The current operator-facing bring-up sheet is derived from:

- `deployment_launch_plan`
- `deployment_readiness`
- `deployment_command_manifest`

It provides:

- launch order
- current per-step readiness
- whether the step has a repo-owned command
- the exact command to run when available
- any current blocking reasons

Use:

```text
python scripts/print_bringup_sheet.py --config configs/dev.yaml
python scripts/print_bringup_sheet.py --config configs/sim.yaml
python scripts/print_bringup_sheet.py --config configs/edge.yaml
```

## What This Layer Does Not Automate

This layer does not yet:

- start services automatically
- keep services running
- restart failed services
- package services for Orin NX
- manage hardware dependencies

It only centralizes:

- repo-owned command knowledge
- command-to-step mapping
- operator-facing guided bring-up output

For the post-start verification layer built on top of this command mapping, see:

- `docs/DEPLOYMENT_VERIFICATION_MANIFEST_CONTRACT.md`
