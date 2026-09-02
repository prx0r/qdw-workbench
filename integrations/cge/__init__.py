"""CGE Integration — wraps mwgym CGE for private-lab.

MWGym lives at /root/mwgym/.
This module provides the CGE adversary, curriculum, and world compilation.
"""
from __future__ import annotations

import sys
from pathlib import Path

_mwgym_root = str(Path("/root/mwgym"))
if _mwgym_root not in sys.path:
    sys.path.insert(0, _mwgym_root)

try:
    from mwgym.worlds.cge_adapter import compile_world, BaseWorld
    from mwgym.worlds.adversary import Adversary
    from mwgym.worlds.curriculum import Curriculum, CurriculumConfig
    from mwgym.schema.world import WorldGenome, FailureVector
    CGE_AVAILABLE = True
except ImportError:
    CGE_AVAILABLE = False

    def compile_world(*args, **kwargs):
        raise RuntimeError("MWGym not available at /root/mwgym/")

    class BaseWorld:
        pass

    class Adversary:
        pass

    class Curriculum:
        pass

    class CurriculumConfig:
        pass

    class WorldGenome:
        pass

    class FailureVector:
        pass


__all__ = [
    "CGE_AVAILABLE",
    "compile_world",
    "BaseWorld",
    "Adversary",
    "Curriculum",
    "CurriculumConfig",
    "WorldGenome",
    "FailureVector",
]
