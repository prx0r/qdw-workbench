"""CG Integration — thin wrapper around /root/cg/cogym_kernel.

The CG kernel lives at /root/cg/cogym_kernel/.
This module provides a clean import interface for private-lab.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure CG kernel is importable
_cg_root = str(Path("/root/cg"))
if _cg_root not in sys.path:
    sys.path.insert(0, _cg_root)

try:
    from cogym_kernel.evo.recipes import propose_children, evolve_population
    from cogym_kernel.evo.suite import EvaluationSuite
    from cogym_kernel.kernel.runner import run_world
    CG_AVAILABLE = True
except ImportError:
    CG_AVAILABLE = False

    def propose_children(*args, **kwargs):
        raise RuntimeError("CG kernel not available at /root/cg/cogym_kernel/")

    def evolve_population(*args, **kwargs):
        raise RuntimeError("CG kernel not available at /root/cg/cogym_kernel/")

    class EvaluationSuite:
        pass

    def run_world(*args, **kwargs):
        raise RuntimeError("CG kernel not available at /root/cg/cogym_kernel/")


__all__ = [
    "CG_AVAILABLE",
    "propose_children",
    "evolve_population",
    "EvaluationSuite",
    "run_world",
]
