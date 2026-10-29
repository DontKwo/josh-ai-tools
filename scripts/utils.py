import os
import platform
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"


def get_user_home() -> Path:
    return Path(os.environ.get("USERPROFILE" if IS_WINDOWS else "HOME", Path.home()))
