"""HTTP client helper.

Tries to use requests if installed, otherwise falls back to urllib.
This keeps the template runnable in a bare Python environment.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple


def get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout_s: int = 30) -> Tuple[int, Any]:
    try:
        import requests  # type: ignore
        r = requests.get(url, headers=headers, timeout=timeout_s)
        return r.status_code, r.json()
    except ModuleNotFoundError:
        return _urllib_get_json(url, headers=headers, timeout_s=timeout_s)


def _urllib_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout_s: int = 30) -> Tuple[int, Any]:
    import urllib.request
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        status = getattr(resp, "status", 200)
        data = resp.read().decode("utf-8", errors="replace")
        return status, json.loads(data)
