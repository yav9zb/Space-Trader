"""Resolves where settings, saves, and logs should live.

When running from source, everything stays relative to the working
directory (repo root) as before - convenient for development. When
running as a packaged build (PyInstaller sets sys.frozen), a bundled
app's own directory can be read-only (macOS .app after signing) or
require admin rights to write to (Program Files on Windows), so user
data instead goes to the OS-appropriate per-user data directory.
"""

import os
import sys
import platform

APP_NAME = "SpaceTrader"


def is_frozen() -> bool:
    """Whether this is running as a packaged (PyInstaller) build."""
    return getattr(sys, 'frozen', False)


def get_user_data_dir() -> str:
    """Get a writable, OS-appropriate directory for settings/saves/logs.

    Returns "." (the working directory) when running from source.
    """
    if not is_frozen():
        return "."

    system = platform.system()
    if system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def get_user_data_path(filename: str) -> str:
    """Get the full path for a user data file (e.g. "settings.json")."""
    return os.path.join(get_user_data_dir(), filename)


def get_resource_path(relative_path: str) -> str:
    """Get the path to a bundled, read-only resource (e.g. "assets/audio/sfx").

    Works both running from source (relative to the working directory) and
    as a PyInstaller build, where bundled data is extracted to sys._MEIPASS
    (onefile) or sits next to the executable (onedir).
    """
    if is_frozen():
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)
