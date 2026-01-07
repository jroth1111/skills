from __future__ import annotations

import ast
from pathlib import Path
from typing import Set


def imported_top_levels(py_path: Path) -> Set[str]:
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    mods: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split(".")[0])
    return mods
