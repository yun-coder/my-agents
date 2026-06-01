"""允许直接运行每章 demo.py 时导入 shared 包。"""

from __future__ import annotations

import sys
from pathlib import Path


def add_phase_root_to_path(script_file: str) -> Path:
    phase_root = Path(script_file).resolve().parent.parent
    if str(phase_root) not in sys.path:
        sys.path.insert(0, str(phase_root))
    return phase_root
