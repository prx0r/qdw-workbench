"""Bittensor module adapter — reads bitt status without modifying bitt.

This adapter reads from bitt's public APIs and data files to report
module status to Private Lab. It never writes to bitt.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from lab.modules import ModuleStatus, ModuleProgram, ModulePerformance


BITT_PATH = Path("/root/bitt")


def read_bitt_status() -> ModuleStatus:
    """Read bitt's current status from its data files and APIs."""
    programs = []

    # Read subnet intel files
    subnets_dir = BITT_PATH / "subnets"
    if subnets_dir.exists():
        for subnet_dir in subnets_dir.iterdir():
            if subnet_dir.is_dir():
                intel_file = subnet_dir / "intel.json"
                if intel_file.exists():
                    try:
                        intel = json.loads(intel_file.read_text())
                        prog = _intel_to_program(subnet_dir.name, intel)
                        if prog:
                            programs.append(prog)
                    except Exception:
                        pass

    # Read scanner store for latest captures
    scanner_db = BITT_PATH / "scanner_store.db"
    captures = []
    if scanner_db.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(scanner_db))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM captures ORDER BY block_number DESC LIMIT 10"
            ).fetchall()
            captures = [dict(r) for r in rows]
            conn.close()
        except Exception:
            pass

    return ModuleStatus(
        module_id="bitt",
        module_name="Bittensor",
        programs=programs,
        metadata={
            "recent_captures": len(captures),
            "latest_block": captures[0].get("block_number", 0) if captures else 0,
        }
    )


def _intel_to_program(subnet_dir_name: str, intel: dict) -> ModuleProgram | None:
    """Convert subnet intel to a ModuleProgram."""
    # Extract subnet number from dir name (e.g., "sn60-bitsec" -> 60)
    parts = subnet_dir_name.split("-")
    if len(parts) < 1:
        return None

    sn_num = parts[0].replace("sn", "")
    name = " ".join(parts[1:]).title() if len(parts) > 1 else f"Subnet {sn_num}"

    # Map known subnets to capability demands
    capability_demands = {
        "60": {"security": 0.99, "smart_contract": 0.94, "vulnerability_detection": 0.98},
        "62": {"software_engineering": 0.95, "swe_coding": 0.9, "testing": 0.85},
        "61": {"security": 0.8, "adversarial": 0.9, "red_team": 0.85},
        "118": {"memory": 0.9, "tool_judgment": 0.85, "reasoning": 0.8},
        "67": {"research": 0.95, "web_search": 0.9, "synthesis": 0.85},
        "6": {"forecasting": 0.95, "probability": 0.9, "calibration": 0.85},
        "15": {"shopping": 0.9, "recommendation": 0.85, "commerce": 0.8},
    }

    state_map = {
        "60": "LIVE_COMPETE",
        "62": "TRAINING",
        "61": "REPRODUCING",
        "118": "LOCAL_BASELINE",
        "67": "LOCAL_BASELINE",
        "6": "TRAINING",
        "15": "DISCOVERED",
    }

    return ModuleProgram(
        program_id=f"bittensor/sn{sn_num}",
        name=name,
        state=state_map.get(sn_num, "DISCOVERED"),
        capability_demand=capability_demands.get(sn_num, {}),
        our_performance=ModulePerformance(),
        possible_actions=["train", "submit", "hold"],
        metadata={"registration_cost_tao": intel.get("registration_cost_tao", 0)},
    )
