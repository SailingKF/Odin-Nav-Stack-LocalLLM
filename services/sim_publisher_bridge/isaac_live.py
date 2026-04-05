from dataclasses import dataclass
import importlib
import importlib.util
from typing import Dict, Iterator, List, Optional, Sequence

from services.sim_publisher_bridge.isaac_contract import IsaacObservationSource


DEFAULT_REQUIRED_MODULES = (
    "omni.isaac.core",
    "omni.isaac.core.utils.stage",
)


@dataclass(frozen=True)
class IsaacLiveAdapterAvailability:
    available: bool
    required_modules: List[str]
    missing_modules: List[str]
    status: str

    def to_dict(self) -> Dict:
        return {
            "available": self.available,
            "required_modules": list(self.required_modules),
            "missing_modules": list(self.missing_modules),
            "status": self.status,
        }


def get_isaac_live_adapter_availability(
    required_modules: Optional[Sequence[str]] = None,
) -> IsaacLiveAdapterAvailability:
    modules = list(required_modules or DEFAULT_REQUIRED_MODULES)
    missing: List[str] = []
    for module_name in modules:
        try:
            module_spec = importlib.util.find_spec(module_name)
        except ModuleNotFoundError:
            module_spec = None
        if module_spec is None:
            missing.append(module_name)
    return IsaacLiveAdapterAvailability(
        available=not missing,
        required_modules=modules,
        missing_modules=missing,
        status="available" if not missing else "missing_dependencies",
    )


class IsaacLiveObservationSource(IsaacObservationSource):
    def __init__(
        self,
        robot_prim_path: str,
        frame_id: str,
        required_modules: Optional[Sequence[str]] = None,
    ) -> None:
        self._robot_prim_path = robot_prim_path
        self._frame_id = frame_id
        self._required_modules = list(required_modules or DEFAULT_REQUIRED_MODULES)

    @property
    def robot_prim_path(self) -> str:
        return self._robot_prim_path

    @property
    def frame_id(self) -> str:
        return self._frame_id

    def availability(self) -> IsaacLiveAdapterAvailability:
        return get_isaac_live_adapter_availability(self._required_modules)

    def iter_observations(self) -> Iterator[Dict]:
        availability = self.availability()
        if not availability.available:
            missing = ", ".join(availability.missing_modules)
            raise RuntimeError(
                f"Live Isaac adapter is unavailable because required modules are missing: {missing}"
            )

        # Imports stay inside the live path so normal repository use remains import-safe.
        for module_name in self._required_modules:
            importlib.import_module(module_name)

        raise NotImplementedError(
            "Live Isaac observation sampling is not implemented yet. "
            "Fill in simulator-specific sampling for the configured robot prim path."
        )
