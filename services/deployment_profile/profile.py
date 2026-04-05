from typing import Any, Dict, List


_KNOWN_PROFILES = {"dev", "sim", "edge"}


def _expected_pose_provider(profile_name: str) -> str:
    return {
        "dev": "mock",
        "sim": "sim_ingress",
        "edge": "odin_ros",
    }[profile_name]


def _deployment_class(profile_name: str) -> str:
    return {
        "dev": "dev_only",
        "sim": "sim_only",
        "edge": "edge_candidate",
    }[profile_name]


def _recording_expectation(profile_name: str) -> str:
    return {
        "dev": "optional",
        "sim": "optional",
        "edge": "optional_off_by_default",
    }[profile_name]


def _audio_expectation(profile_name: str) -> str:
    return {
        "dev": "mock_or_service_backed",
        "sim": "mock_or_service_backed",
        "edge": "service_backed_or_device_backed",
    }[profile_name]


def _local_llm_expectation(profile_name: str) -> str:
    return {
        "dev": "optional",
        "sim": "optional",
        "edge": "expected",
    }[profile_name]


def _build_mock_components(config: Dict[str, Any]) -> List[str]:
    active: List[str] = []
    if str(config.get("pose_provider_type")) == "mock":
        active.append("mock_pose_provider")
    if str(config.get("narrator_type", "mock")) == "mock":
        active.append("mock_narrator")
    if str(config.get("llm_backend_type", "mock")) == "mock":
        active.append("mock_llm_backend")
    if str(config.get("audio_output_type", "mock")) == "mock":
        active.append("mock_audio_output")
    if str(config.get("tts_backend_type", "mock")) == "mock":
        active.append("mock_tts_backend")
    if str(config.get("artifact_player_backend_type", "mock")) == "mock":
        active.append("mock_artifact_player")
    return active


def _build_placeholder_components(profile_name: str, config: Dict[str, Any]) -> List[str]:
    placeholders: List[str] = []
    if profile_name == "sim" and str((config.get("isaac_source") or {}).get("mode", "stub")) == "stub":
        placeholders.append("isaac_stub_source")
    if profile_name == "edge":
        if str(config.get("narrator_type", "mock")) != "local_llm":
            placeholders.append("non_local_llm_narrator")
        if str(config.get("llm_backend_type", "mock")) == "mock":
            placeholders.append("mock_llm_backend")
        if str(config.get("audio_output_type", "mock")) == "mock":
            placeholders.append("mock_audio_output")
        if str(config.get("tts_backend_type", "mock")) == "mock":
            placeholders.append("mock_tts_backend")
        if str(config.get("artifact_player_backend_type", "mock")) == "mock":
            placeholders.append("mock_artifact_player")
    return placeholders


def build_deployment_profile(config: Dict[str, Any]) -> Dict[str, Any]:
    profile_name = str(config.get("env_name", "")).strip()
    configured_pose_provider = str(config.get("pose_provider_type", ""))
    narrator_type = str(config.get("narrator_type", "mock"))
    audio_output_type = str(config.get("audio_output_type", "mock"))
    llm_backend_type = str(config.get("llm_backend_type", "mock"))
    recording_enabled = bool(config.get("recording_enabled", False))

    errors: List[str] = []
    warnings: List[str] = []

    if profile_name not in _KNOWN_PROFILES:
        errors.append(
            "Unsupported env_name. Expected one of: dev, sim, edge."
        )
        return {
            "profile_name": profile_name or None,
            "deployment_class": "unknown",
            "readiness_status": "invalid",
            "is_edge_ready": False,
            "capabilities": {
                "pose_source_expectation": None,
                "local_llm_expectation": None,
                "audio_mode_expectation": None,
                "recording_expectation": None,
            },
            "configured": {
                "pose_provider_type": configured_pose_provider or None,
                "narrator_type": narrator_type,
                "audio_output_type": audio_output_type,
                "llm_backend_type": llm_backend_type,
                "recording_enabled": recording_enabled,
            },
            "supports": {
                "mock_pose": configured_pose_provider == "mock",
                "sim_pose_ingress": configured_pose_provider == "sim_ingress",
                "hardware_pose": configured_pose_provider == "odin_ros",
                "local_llm": narrator_type == "local_llm",
                "service_backed_audio": audio_output_type == "tts_service",
            },
            "mock_components_active": _build_mock_components(config),
            "placeholder_components": [],
            "errors": errors,
            "warnings": warnings,
        }

    expected_pose_provider = _expected_pose_provider(profile_name)

    if configured_pose_provider != expected_pose_provider:
        errors.append(
            f"{profile_name} profile expects pose_provider_type={expected_pose_provider}, got {configured_pose_provider or '<missing>'}."
        )

    if profile_name == "edge":
        if narrator_type != "local_llm":
            warnings.append("edge profile is still using a non-local-LLM narrator path.")
        if llm_backend_type == "mock":
            warnings.append("edge profile still points at a mock llm backend.")
        if audio_output_type == "mock":
            warnings.append("edge profile still uses mock audio output instead of service/device-backed playback.")
        if audio_output_type == "tts_service" and str(config.get("tts_backend_type", "mock")) == "mock":
            warnings.append("edge profile uses tts_service but the configured tts backend is still mock.")
        if str(config.get("artifact_player_backend_type", "mock")) == "mock":
            warnings.append("edge profile still uses the mock artifact player backend.")

    if profile_name == "sim" and str((config.get("isaac_source") or {}).get("mode", "stub")) == "stub":
        warnings.append("sim profile is still using the Isaac stub source instead of a live simulator adapter.")

    if profile_name == "dev" and configured_pose_provider != "mock":
        warnings.append("dev profile is intended for laptop/mock-first operation.")

    placeholder_components = _build_placeholder_components(profile_name, config)
    if errors:
        readiness_status = "invalid"
    elif profile_name == "edge" and placeholder_components:
        readiness_status = "placeholder"
    else:
        readiness_status = "ready_for_profile"

    return {
        "profile_name": profile_name,
        "deployment_class": _deployment_class(profile_name),
        "readiness_status": readiness_status,
        "is_edge_ready": profile_name == "edge" and readiness_status == "ready_for_profile",
        "capabilities": {
            "pose_source_expectation": expected_pose_provider,
            "local_llm_expectation": _local_llm_expectation(profile_name),
            "audio_mode_expectation": _audio_expectation(profile_name),
            "recording_expectation": _recording_expectation(profile_name),
        },
        "configured": {
            "pose_provider_type": configured_pose_provider,
            "narrator_type": narrator_type,
            "audio_output_type": audio_output_type,
            "llm_backend_type": llm_backend_type,
            "recording_enabled": recording_enabled,
        },
        "supports": {
            "mock_pose": configured_pose_provider == "mock",
            "sim_pose_ingress": configured_pose_provider == "sim_ingress",
            "hardware_pose": configured_pose_provider == "odin_ros",
            "local_llm": narrator_type == "local_llm",
            "service_backed_audio": audio_output_type == "tts_service",
        },
        "mock_components_active": _build_mock_components(config),
        "placeholder_components": placeholder_components,
        "errors": errors,
        "warnings": warnings,
    }
