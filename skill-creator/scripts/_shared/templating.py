from __future__ import annotations

from pathlib import Path
from typing import Dict


def render(text: str, variables: Dict[str, str]) -> str:
    out = text
    for k, v in variables.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def copy_template_tree(template_root: Path, dest_root: Path, variables: Dict[str, str]) -> None:
    for src in template_root.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(template_root)
        name = rel.name[:-4] if rel.name.endswith(".tpl") else rel.name
        out_path = dest_root / rel.parent / name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render(src.read_text(encoding="utf-8"), variables), encoding="utf-8")
