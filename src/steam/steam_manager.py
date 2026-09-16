"""Thin, optional Steamworks integration.

IMPORTANT - read before relying on this: this module was written without
access to the actual Steamworks SDK (it requires a Steam partner account
to download, which this codebase doesn't have) and has NEVER been tested
against a real steam_api library. The function signature below is based
on Valve's current public documentation for SteamAPI_InitFlat(), the
entry point intended for exactly this use case (loading the SDK
dynamically via ctypes rather than linking its C++ headers) - but Valve
has broken this API before without a changelog mention (SDK 1.59, Feb
2024, replaced the older SteamAPI_Init() this way). Whoever adds the
real SDK must verify this against the actual steam_api_flat.h /
steam_api_common.h headers for the SDK version in use, and fix anything
that's drifted, before shipping.

By design this degrades to a total no-op everywhere the native Steamworks
library isn't present - which is every environment except a real Steam
install with steam_appid.txt (dev) or launched via Steam (release). The
game must work identically with or without it.
"""

import ctypes
import os
import platform


def _find_steam_library():
    """Locate the native Steamworks library next to the executable, if present."""
    system = platform.system()
    if system == "Windows":
        candidates = ["steam_api64.dll", "steam_api.dll"]
    elif system == "Darwin":
        candidates = ["libsteam_api.dylib"]
    else:
        candidates = ["libsteam_api.so"]

    search_dir = os.path.dirname(os.path.abspath(__file__))
    # Also check the working directory (dev mode) and the executable's directory
    search_dirs = [os.path.abspath("."), search_dir]

    for directory in search_dirs:
        for name in candidates:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                return path
    return None


class SteamManager:
    """Initializes/shuts down the Steamworks API if it's available. Always safe to use."""

    def __init__(self):
        self.enabled = False
        self._lib = None
        self._init()

    def _init(self):
        library_path = _find_steam_library()
        if not library_path:
            return  # Not running under Steam / no SDK present - normal case

        try:
            self._lib = ctypes.CDLL(library_path)

            # SteamAPI_InitFlat(SteamErrMsg *pOutErrMsg) -> ESteamAPIInitResult
            # k_cchMaxSteamErrMsg is 1024 as of recent SDKs - VERIFY against
            # the real SDK header (see module docstring).
            err_msg = ctypes.create_string_buffer(1024)
            self._lib.SteamAPI_InitFlat.restype = ctypes.c_int32
            result = self._lib.SteamAPI_InitFlat(err_msg)

            if result == 0:  # k_ESteamAPIInitResult_OK
                self.enabled = True
                print("Steamworks initialized")
            else:
                print(f"Steamworks init failed (result={result}): {err_msg.value.decode(errors='replace')}")
        except (OSError, AttributeError) as e:
            print(f"Steamworks unavailable: {e}")
            self._lib = None

    def shutdown(self):
        """Shut down the Steamworks API. Safe to call even if never initialized."""
        if self.enabled and self._lib:
            try:
                self._lib.SteamAPI_Shutdown()
            except (OSError, AttributeError):
                pass
        self.enabled = False


# Global Steam manager instance
steam_manager = SteamManager()
