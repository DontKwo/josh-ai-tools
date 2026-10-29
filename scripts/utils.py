<<<<<<< HEAD
"""Shared utility functions for scripts."""
from __future__ import annotations

from pathlib import Path


def format_command_path(path: Path) -> str:
    path_str = str(path)
    if " " in path_str:
        return f'"{path_str}"'
    return path_str
=======
import os
import platform
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"


def get_user_home() -> Path:
    return Path(os.environ.get("USERPROFILE" if IS_WINDOWS else "HOME", Path.home()))
>>>>>>> origin/deduplicate-get-user-home-16529137994297347276
