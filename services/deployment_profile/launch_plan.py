from typing import Any, Dict, List


def _step(
    step_id: str,
    order: int,
    category: str,
    required: bool,
    name: str,
    startup_hint: str,
    readiness_gates: List[str],
    detail: str,
) -> Dict[str, Any]:
    return {
        "step_id": step_id,
        "order": order,
        "category": category,
        "required": required,
        "name": name,
        "startup_hint": startup_hint,
        "readiness_gates": readiness_gates,
        "detail": detail,
    }


def _dev_plan(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    narrator_type = str(config.get("narrator_type", "mock"))
    llm_backend_type = str(config.get("llm_backend_type", "mock"))

    if narrator_type == "local_llm" and llm_backend_type == "ollama":
        steps.append(
            _step(
                "ollama_runtime",
                10,
                "external_dependency",
                True,
                "Start local Ollama runtime",
                "Ensure the local Ollama runtime is serving before repo-owned LLM services start.",
                ["deployment_preflight.ollama_runtime=ok"],
                "This dependency is external to the repo but is required when dev uses the Ollama-backed local_llm path.",
            )
        )

    if narrator_type == "local_llm":
        steps.append(
            _step(
                "llm_gateway",
                20,
                "internal_service",
                True,
                "Start llm gateway",
                "Run scripts/run_llm_gateway.py with the selected config before starting the API server.",
                ["deployment_preflight.llm_gateway=ok"],
                "The gateway is repo-owned and should be up before the API server if real local_llm responses are expected.",
            )
        )

    steps.append(
        _step(
            "api_server",
            30,
            "internal_service",
            True,
            "Start local API server",
            "Run scripts/run_api_server.py after required dependencies are available.",
            ["deployment_preflight.route_file=ok", "deployment_preflight.poi_file=ok", "deployment_preflight.session_log_dir=ok"],
            "This is the main repo-owned operator surface for desktop and Android-browser debugging.",
        )
    )
    steps.append(
        _step(
            "debug_browser",
            40,
            "optional_service",
            False,
            "Open debug page",
            "Open /debug in a desktop or Android browser after the API server is ready.",
            ["api_server reachable"],
            "This is optional but recommended for operator visibility and control-path validation.",
        )
    )
    return steps


def _sim_plan(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    isaac_mode = str((config.get("isaac_source") or {}).get("mode", "stub"))

    if isaac_mode == "live":
        steps.append(
            _step(
                "isaac_live_dependency",
                10,
                "external_dependency",
                True,
                "Start live Isaac simulator source",
                "Bring up the external simulator/runtime that will publish live observations before bridge services depend on it.",
                ["deployment_preflight.isaac_live_dependency=unverified_external"],
                "This dependency remains external/manual in the current repo and is not auto-managed by the launch plan.",
            )
        )
    else:
        steps.append(
            _step(
                "isaac_stub_source",
                10,
                "optional_service",
                False,
                "Use Isaac stub payload source",
                "The configured sim profile can use the repo stub source for dry-run validation without a live simulator.",
                [],
                "This is optional because it replaces the external live simulator during laptop validation.",
            )
        )

    steps.append(
        _step(
            "sim_pose_ingress_server",
            20,
            "internal_service",
            True,
            "Start sim pose ingress server",
            "Run scripts/run_sim_pose_ingress_server.py before pushing simulator pose payloads.",
            ["deployment_preflight.route_file=ok", "deployment_preflight.poi_file=ok", "deployment_preflight.session_log_dir=ok"],
            "This repo-owned service receives simulator pose payloads and drives the tour runtime for sim validation.",
        )
    )
    steps.append(
        _step(
            "sim_publisher_bridge",
            30,
            "optional_service",
            False,
            "Start simulator publisher bridge",
            "Use the publisher bridge scripts only when validating Isaac-style payload projection and HTTP publishing.",
            ["sim_pose_ingress_server ready"],
            "This step is optional because stub or direct HTTP posting can validate the sim path without the full bridge runtime.",
        )
    )
    steps.append(
        _step(
            "api_server",
            40,
            "optional_service",
            False,
            "Start local API/debug server",
            "Run scripts/run_api_server.py if operator-facing API or /debug visibility is needed during sim work.",
            ["deployment_preflight.route_file=ok", "deployment_preflight.poi_file=ok"],
            "This is optional for sim because the dedicated sim ingress path can be validated without the API server.",
        )
    )
    return steps


def _edge_plan(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    llm_backend_type = str(config.get("llm_backend_type", "mock"))
    audio_output_type = str(config.get("audio_output_type", "mock"))

    steps.append(
        _step(
            "hardware_pose_dependency",
            10,
            "external_dependency",
            True,
            "Ensure hardware pose source is available",
            "Bring up the external odin_ros pose source before API-level control paths depend on live robot position.",
            ["deployment_preflight.hardware_pose_dependency=unverified_external"],
            "This remains a manual/external bring-up step in the current repo.",
        )
    )

    if llm_backend_type == "ollama":
        steps.append(
            _step(
                "ollama_runtime",
                20,
                "external_dependency",
                True,
                "Ensure local Ollama runtime is available",
                "Start the local LLM runtime before repo-owned gateway services that depend on it.",
                ["deployment_preflight.ollama_runtime=ok"],
                "This external dependency is required for the current edge local_llm path.",
            )
        )

    steps.append(
        _step(
            "llm_gateway",
            30,
            "internal_service",
            True,
            "Start llm gateway",
            "Run scripts/run_llm_gateway.py after external LLM dependencies are ready.",
            ["deployment_preflight.llm_gateway=ok"],
            "The gateway is repo-owned, but it still depends on upstream local runtime availability.",
        )
    )
    steps.append(
        _step(
            "api_server",
            40,
            "internal_service",
            True,
            "Start backend API server",
            "Run scripts/run_api_server.py after hardware pose and LLM dependencies are in their expected state.",
            ["deployment_preflight.route_file=ok", "deployment_preflight.poi_file=ok", "deployment_preflight.session_log_dir=ok"],
            "This is the primary repo-owned control surface for Android/browser clients on edge.",
        )
    )
    steps.append(
        _step(
            "audio_device_dependency",
            50,
            "external_dependency" if audio_output_type != "mock" else "optional_service",
            audio_output_type != "mock",
            "Verify audio output path",
            "Confirm real playback device readiness when the edge profile moves beyond mock audio output.",
            ["deployment_preflight.audio_device_dependency"],
            "In the current edge config this step stays mock/not-applicable, but future real playback will make it an external dependency.",
        )
    )
    return steps


def build_deployment_launch_plan(config: Dict[str, Any]) -> Dict[str, Any]:
    profile_name = str(config.get("env_name", "")).strip()
    if profile_name == "dev":
        steps = _dev_plan(config)
    elif profile_name == "sim":
        steps = _sim_plan(config)
    elif profile_name == "edge":
        steps = _edge_plan(config)
    else:
        steps = []

    return {
        "profile_name": profile_name or None,
        "automation_level": "manual_guided",
        "steps": steps,
        "step_count": len(steps),
        "required_step_count": sum(1 for item in steps if item.get("required")),
        "categories": sorted({str(item["category"]) for item in steps}),
    }
