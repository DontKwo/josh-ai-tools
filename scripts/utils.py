"""Shared utility functions for scripts."""
from __future__ import annotations

from pathlib import Path


def format_command_path(path: Path) -> str:
    path_str = str(path)
    if " " in path_str:
        return f'"{path_str}"'
    return path_str
