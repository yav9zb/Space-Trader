"""The ending: built from the choices the player made. Pure functions over the
story flags, so every combination can be checked without a game running.
Plain ASCII only.
"""

from dataclasses import dataclass
from typing import List

PATHS = ("expose", "join", "independent")
SIGNALS = ("open", "sealed")


@dataclass(frozen=True)
class Ending:
    title: str
    paragraphs: List[str]


_TITLES = {
    ("expose", "open"): "The Open Sky",
    ("expose", "sealed"): "The Quiet Reckoning",
    ("join", "open"): "The Gate Unbarred",
    ("join", "sealed"): "The Guild's Century",
    ("independent", "open"): "Free Lanes",
    ("independent", "sealed"): "The Patient Peace",
}

_PATH_TEXT = {
    "expose": (
        "You put the Hollow Account in front of every station in the sector. "
        "The Guild's charter was rewritten under public pressure, Director "
        "Marrow resigned before he could be removed, and the pirate captains "
        "he paid scattered without a paymaster. The lanes are still "
        "dangerous. They are no longer dangerous on purpose."
    ),
    "join": (
        "You took Marrow's seat, and the lanes grew quiet. Guild patrols "
        "reach into the old pirate sectors and insurance premiums have "
        "halved. Some independent stations signed Guild charters because they "
        "had no choice. You are not sure whether you built a safe galaxy or "
        "a very orderly one."
    ),
    "independent": (
        "You brokered a truce nobody loved. The Guild stopped paying the "
        "raiders, the raiders stopped hunting the Guild, and the independent "
        "stations kept their flags. It is slow and fragile and it holds, one "
        "quiet cargo run at a time."
    ),
}

_SIGNAL_TEXT = {
    "open": (
        "You opened the Signal to everyone. Within a month every faction had "
        "a copy of the chart, and traders were fanning out past the old "
        "edge of the map. Nobody owns what lies beyond it, which is "
        "exactly how Vane would have wanted it."
    ),
    "sealed": (
        "You sealed the Signal. Dr. Okoye keeps listening, and a handful of "
        "people know what it says. One day it will have to be shared, but "
        "not before someone understands what is waiting at the other end of "
        "that chart."
    ),
}

_EPILOGUE = (
    "Hale hung Jessup Vane's ledger over the dock office desk, every page "
    "decoded. He says he will fly Vane's old route himself one day, if his "
    "knees allow. Until then, the ship is yours, captain, and the "
    "map is wider than it has ever been."
)


def ending_path(flags) -> str:
    for path in PATHS:
        if flags.get(f"path_{path}"):
            return path
    return "independent"          # a save that predates the choice flags


def ending_signal(flags) -> str:
    return "sealed" if flags.get("signal_sealed") and not flags.get("signal_open") else "open"


def build_ending(flags) -> Ending:
    path, signal = ending_path(flags), ending_signal(flags)
    return Ending(
        title=_TITLES[(path, signal)],
        paragraphs=[_PATH_TEXT[path], _SIGNAL_TEXT[signal], _EPILOGUE],
    )
