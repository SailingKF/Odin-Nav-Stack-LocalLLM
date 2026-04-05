from typing import Any, Dict, List, Optional


def _default_config_path(profile_name: Optional[str]) -> Optional[str]:
    if not profile_name:
        return None
    return f"configs/{profile_name}.yaml"


def _command_entry(
    command_id: str,
    step: Dict[str, Any],
    entrypoint_path: str,
    argv: List[str],
    description: str,
    config_path: Optional[str],
) -> Dict[str, Any]:
    return {
        "command_id": command_id,
        "step_id": step.get("step_id"),
        "order": step.get("order"),
        "profile_name": step.get("profile_name"),
        "command_kind": "python_script",
        "entrypoint_path": entrypoint_path,
        "argv": argv,
        "display_command": " ".join(argv),
        "config_path": config_path,
        "description": description,
        "owned_by_repo": True,
    }


def _build_known_command(step: Dict[str, Any], config_path: Optional[str]) -> Optional[Dict[str, Any]]:
    step_id = str(step.get("step_id"))
    command_id = f"{step_id}_command"

    if step_id == "llm_gateway":
        argv = ["python", "scripts/run_llm_gateway.py"]
        if config_path:
            argv.extend(["--config", config_path])
        return _command_entry(
            command_id,
            step,
            "scripts/run_llm_gateway.py",
            argv,
            "Start the repo-owned local LLM gateway for narrator traffic.",
            config_path,
        )

    if step_id == "api_server":
        argv = ["python", "scripts/run_api_server.py"]
        if config_path:
            argv.extend(["--config", config_path])
        return _command_entry(
            command_id,
            step,
            "scripts/run_api_server.py",
            argv,
            "Start the operator-facing backend API and /debug control surface.",
            config_path,
        )

    if step_id == "sim_pose_ingress_server":
        argv = ["python", "scripts/run_sim_pose_ingress_server.py"]
        if config_path:
            argv.extend(["--config", config_path])
        return _command_entry(
            command_id,
            step,
            "scripts/run_sim_pose_ingress_server.py",
            argv,
            "Start the sim pose ingress HTTP bridge that drives the tour runtime from simulator poses.",
            config_path,
        )

    return None


def build_deployment_command_manifest(
    config: Dict[str, Any],
    deployment_launch_plan: Dict[str, Any],
) -> Dict[str, Any]:
    profile_name = str(config.get("env_name", "")).strip() or None
    config_path = _default_config_path(profile_name)
    steps = list(deployment_launch_plan.get("steps") or [])

    commands: List[Dict[str, Any]] = []
    step_actions: List[Dict[str, Any]] = []

    for step in steps:
        step_with_profile = dict(step)
        step_with_profile["profile_name"] = profile_name
        command = _build_known_command(step_with_profile, config_path)

        if command is not None:
            commands.append(command)
            action_type = "repo_command"
            operator_action = command["display_command"]
        elif step.get("category") == "external_dependency":
            action_type = "manual_external"
            operator_action = None
        else:
            action_type = "manual_optional"
            operator_action = None

        step_actions.append(
            {
                "step_id": step.get("step_id"),
                "order": step.get("order"),
                "name": step.get("name"),
                "category": step.get("category"),
                "required": bool(step.get("required")),
                "action_type": action_type,
                "command_available": command is not None,
                "command_id": command.get("command_id") if command else None,
                "operator_action": operator_action,
                "detail": step.get("detail"),
                "startup_hint": step.get("startup_hint"),
            }
        )

    return {
        "profile_name": profile_name,
        "automation_level": deployment_launch_plan.get("automation_level", "manual_guided"),
        "config_path": config_path,
        "commands": commands,
        "steps": step_actions,
        "command_count": len(commands),
        "repo_command_step_count": sum(1 for item in step_actions if item.get("command_available")),
        "manual_step_count": sum(1 for item in step_actions if not item.get("command_available")),
    }


def build_guided_bringup_sheet(
    deployment_launch_plan: Dict[str, Any],
    deployment_readiness: Dict[str, Any],
    deployment_command_manifest: Dict[str, Any],
) -> Dict[str, Any]:
    readiness_by_step = {
        str(item.get("step_id")): item
        for item in list(deployment_readiness.get("steps") or [])
        if item.get("step_id")
    }
    command_by_step = {
        str(item.get("step_id")): item
        for item in list(deployment_command_manifest.get("commands") or [])
        if item.get("step_id")
    }

    guided_steps: List[Dict[str, Any]] = []
    for step in list(deployment_launch_plan.get("steps") or []):
        step_id = str(step.get("step_id"))
        readiness = readiness_by_step.get(step_id, {})
        command = command_by_step.get(step_id)
        guided_steps.append(
            {
                "step_id": step_id,
                "order": step.get("order"),
                "name": step.get("name"),
                "required": bool(step.get("required")),
                "category": step.get("category"),
                "status": readiness.get("status"),
                "action_type": "repo_command" if command else (
                    "manual_external" if step.get("category") == "external_dependency" else "manual_optional"
                ),
                "display_command": command.get("display_command") if command else None,
                "entrypoint_path": command.get("entrypoint_path") if command else None,
                "startup_hint": step.get("startup_hint"),
                "blocking_reasons": list(readiness.get("blocking_reasons") or []),
            }
        )

    return {
        "profile_name": deployment_command_manifest.get("profile_name"),
        "config_path": deployment_command_manifest.get("config_path"),
        "overall_status": deployment_readiness.get("overall_status"),
        "blocking_reasons": list(deployment_readiness.get("blocking_reasons") or []),
        "steps": guided_steps,
        "step_count": len(guided_steps),
        "command_count": deployment_command_manifest.get("command_count", 0),
    }
