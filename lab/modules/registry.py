"""Module registry — discover and track modules that report to Private Lab.

Modules own their ecosystems. The registry tracks what modules exist
and their current status.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from lab.modules import ModuleStatus, ModuleProgram


REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "module_registry.json"


class ModuleRegistry:
    """Track modules that report to Private Lab."""

    def __init__(self):
        self.modules: dict[str, ModuleStatus] = {}
        self._load()

    def _load(self):
        if REGISTRY_PATH.exists():
            try:
                data = json.loads(REGISTRY_PATH.read_text())
                for mid, mdata in data.items():
                    self.modules[mid] = ModuleStatus(**mdata)
            except Exception:
                pass

    def _save(self):
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {mid: m.model_dump() for mid, m in self.modules.items()}
        REGISTRY_PATH.write_text(json.dumps(data, indent=2, default=str))

    def register_module(self, status: ModuleStatus):
        """Register or update a module's status."""
        self.modules[status.module_id] = status
        self._save()

    def get_module(self, module_id: str) -> ModuleStatus | None:
        return self.modules.get(module_id)

    def list_modules(self) -> list[ModuleStatus]:
        return list(self.modules.values())

    def get_all_programs(self) -> list[tuple[str, ModuleProgram]]:
        """Get all programs across all modules."""
        programs = []
        for mid, status in self.modules.items():
            for prog in status.programs:
                programs.append((mid, prog))
        return programs

    def get_programs_by_state(self, state: str) -> list[tuple[str, ModuleProgram]]:
        """Get programs in a specific state."""
        return [(mid, p) for mid, p in self.get_all_programs() if p.state == state]

    def get_programs_by_pool(self, pool_id: str) -> list[tuple[str, ModuleProgram]]:
        """Get programs that consume from a specific pool."""
        results = []
        for mid, prog in self.get_all_programs():
            if pool_id in prog.capability_demand:
                results.append((mid, prog))
        return results

    def summary(self) -> dict:
        """Get a summary of all modules."""
        modules = []
        for mid, status in self.modules.items():
            modules.append({
                "module_id": mid,
                "name": status.module_name,
                "programs": len(status.programs),
                "total_cost": status.total_cost_usd,
                "total_revenue": status.total_revenue_usd,
                "states": [p.state for p in status.programs],
            })
        return {"modules": modules, "total": len(self.modules)}
