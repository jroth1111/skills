from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Union, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

FRONTMATTER_DELIM = re.compile(r"^---\s*$")
SPEC_TOP_LEVEL_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
EXTENSION_KEYS = {
    "model",
    "dependencies",
    "version",
}
KNOWN_TOP_LEVEL_KEYS = SPEC_TOP_LEVEL_KEYS | EXTENSION_KEYS
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED = {"anthropic", "claude"}
XML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class Frontmatter:
    data: Dict[str, Union[str, List[str], Dict[str, str]]]
    start_line: int
    end_line: int
    warnings: List[str] = field(default_factory=list)


def _parse_yaml_frontmatter(
    fm_text: str,
) -> Tuple[Optional[Dict[str, Union[str, List[str], Dict[str, str]]]], Optional[str]]:
    if yaml is None:
        return None, None
    try:
        data = yaml.safe_load(fm_text)
    except Exception as exc:
        return None, f"YAML frontmatter parse error: {exc}"
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "YAML frontmatter must be a mapping"
    coerced: Dict[str, Union[str, List[str], Dict[str, str]]] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            return None, "YAML frontmatter keys must be strings"
        coerced[key] = value
    return coerced, None


def extract_frontmatter(md_text: str) -> Optional[Frontmatter]:
    lines = md_text.splitlines()
    if not lines or not FRONTMATTER_DELIM.match(lines[0]):
        return None
    end = None
    for i in range(1, len(lines)):
        if FRONTMATTER_DELIM.match(lines[i]):
            end = i
            break
    if end is None:
        return None
    fm_lines = lines[1:end]
    fm_text = "\n".join(fm_lines)
    warnings: List[str] = []
    yaml_data, yaml_error = _parse_yaml_frontmatter(fm_text)
    if yaml_error:
        warnings.append(f"{yaml_error}. Falling back to lenient parser.")
    if yaml_data is not None:
        return Frontmatter(data=yaml_data, start_line=0, end_line=end, warnings=warnings)
    data: Dict[str, Union[str, List[str]]] = {}
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if line.startswith((" ", "\t")):
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2)

        if value in ("|", ">"):
            block_lines: List[str] = []
            i += 1
            while i < len(fm_lines) and fm_lines[i].startswith((" ", "\t")):
                block_lines.append(fm_lines[i].lstrip())
                i += 1
            data[key] = "\n".join(block_lines).strip()
            continue

        if value == "":
            block_lines: List[str] = []
            j = i + 1
            while j < len(fm_lines) and fm_lines[j].startswith((" ", "\t")):
                block_lines.append(fm_lines[j])
                j += 1

            stripped_lines = [line.lstrip() for line in block_lines if line.strip()]
            first = stripped_lines[0] if stripped_lines else ""

            if first.startswith("- "):
                list_items: List[str] = []
                for line in block_lines:
                    lstrip = line.lstrip()
                    if not lstrip:
                        continue
                    if lstrip.startswith("- "):
                        list_items.append(lstrip[2:].strip())
                    else:
                        list_items.append(lstrip.strip())
                data[key] = list_items
                i = j
                continue

            map_items: Dict[str, str] = {}
            for line in block_lines:
                lstrip = line.lstrip()
                if not lstrip or lstrip.startswith("#"):
                    continue
                m = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", lstrip)
                if m:
                    map_items[m.group(1)] = m.group(2).strip()
            if map_items:
                data[key] = map_items
                i = j
                continue
            if block_lines:
                data[key] = "\n".join(line.lstrip() for line in block_lines).strip()
                i = j
                continue

            data[key] = ""
            i += 1
            continue

        data[key] = value
        i += 1
    return Frontmatter(data=data, start_line=0, end_line=end, warnings=warnings)


def validate_frontmatter(
    data: Dict[str, Union[str, List[str], Dict[str, str]]]
) -> tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    unknown = set(data.keys()) - KNOWN_TOP_LEVEL_KEYS
    if unknown:
        warnings.append(
            "Unknown frontmatter keys (treated as extensions): {}".format(sorted(unknown))
        )
    name_value = data.get("name", "")
    name = name_value.strip() if isinstance(name_value, str) else ""
    if not name or not isinstance(name_value, str):
        errors.append("Missing required frontmatter field: name")
    else:
        if len(name) > 64:
            errors.append("Invalid name. Must be 1-64 characters")
        if not NAME_RE.match(name):
            errors.append("Invalid name. Use lowercase letters, numbers, and single hyphens only")
        if XML_TAG_RE.search(name):
            errors.append("Invalid name: must not contain XML tags")
        lowered = name.lower()
        if any(r in lowered for r in RESERVED):
            errors.append('Invalid name: must not contain reserved words "anthropic" or "claude"')
    desc_value = data.get("description", "")
    desc = desc_value.strip() if isinstance(desc_value, str) else ""
    if not desc or not isinstance(desc_value, str):
        errors.append("Missing required frontmatter field: description")
    else:
        if len(desc) > 1024:
            errors.append("Description too long (>1024 characters)")
        if XML_TAG_RE.search(desc):
            errors.append("Invalid description: must not contain XML tags")
    compatibility = data.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            errors.append("Invalid compatibility: must be a string")
        else:
            compat = compatibility.strip()
            if not compat:
                errors.append("Invalid compatibility: must be 1-500 characters")
            elif len(compat) > 500:
                errors.append("Compatibility too long (>500 characters)")
    metadata = data.get("metadata")
    if metadata is not None:
        if isinstance(metadata, dict):
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()):
                errors.append("Invalid metadata: keys and values must be strings")
        elif isinstance(metadata, str):
            warnings.append("Metadata should be a mapping; inline forms may not be fully parsed")
        else:
            errors.append("Invalid metadata: must be a mapping of string keys to string values")
    allowed_tools = data.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, (str, list)):
        errors.append("Invalid allowed-tools: must be a string or list")
    dependencies = data.get("dependencies")
    if dependencies is not None and not isinstance(dependencies, (str, list)):
        errors.append("Invalid dependencies: must be a string or list")
    version = data.get("version")
    if version is not None and not isinstance(version, str):
        errors.append("Invalid version: must be a string")
    model = data.get("model")
    if model is not None and not isinstance(model, str):
        errors.append("Invalid model: must be a string")
    license_value = data.get("license")
    if license_value is not None and not isinstance(license_value, str):
        errors.append("Invalid license: must be a string")
    return errors, warnings


def parse_allowed_tools(value: Union[str, List[str], None]) -> List[str]:
    if isinstance(value, list):
        return [v.strip() for v in value if isinstance(v, str) and v.strip()]
    if not isinstance(value, str):
        return []
    raw = value.strip().strip("[]")
    if not raw:
        return []
    raw = raw.replace(",", " ")
    return [p.strip() for p in raw.split() if p.strip()]
