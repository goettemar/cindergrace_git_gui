"""JSON storage helpers for favorites and profiles."""

import json
import os
from typing import Any


def load_json(path: str, default: Any):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def load_list(path: str) -> list:
    data = load_json(path, [])
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, str)]


def save_list(path: str, items: list) -> None:
    seen = set()
    cleaned = []
    for item in items:
        if not isinstance(item, str):
            continue
        if item in seen:
            continue
        seen.add(item)
        cleaned.append(item)
    save_json(path, cleaned)


def load_profiles(path: str) -> dict:
    data = load_json(path, {})
    return data if isinstance(data, dict) else {}


def save_profiles(path: str, profiles: dict) -> None:
    save_json(path, profiles)


__all__ = [
    "load_json",
    "save_json",
    "load_list",
    "save_list",
    "load_profiles",
    "save_profiles",
]
