"""Achievements. Each is a plain condition over the game's saved state (the
story event log and counters, rank, credits, the campaign flags), so there is
no separate bookkeeping to keep in sync. Which ones are unlocked is kept
across games in the legacy file, and each unlock is announced on screen and
passed to Steam when it is available.
"""

import logging
from dataclasses import dataclass
from typing import Callable, List

from .missions.rank_system import RANKS
from .legacy import legacy

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 2.0


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    description: str
    condition: Callable      # (game_engine) -> bool


def _events(name: str):
    return lambda g: g.story_state.count_events(name) >= 1


def _event_count(name: str, count: int):
    return lambda g: g.story_state.count_events(name) >= count


def _rank(name: str):
    return lambda g: g.mission_manager.reputation >= dict(RANKS)[name]


def _flag(name: str):
    return lambda g: g.story_state.has_flag(name)


def _completed(mission_type: str):
    return lambda g: g.story_state.count_events(f"completed_type:{mission_type}") >= 1


ACHIEVEMENTS: List[Achievement] = [
    Achievement("first_blood", "First Blood", "Destroy a pirate ship.",
                _events("bandit_destroyed")),
    Achievement("pirate_bane", "Pirate Bane", "Destroy 25 pirate ships.",
                _event_count("bandit_destroyed", 25)),
    Achievement("licensed", "Licensed", "Earn the rank of Trader.", _rank("Trader")),
    Achievement("captains_bars", "Captain's Bars", "Earn the rank of Captain.", _rank("Captain")),
    Achievement("legend", "Legend", "Earn the rank of Legend.", _rank("Legend")),
    Achievement("wealthy", "Well Off", "Hold 50,000 credits at once.",
                lambda g: g.ship.credits >= 50_000),
    Achievement("reliable", "Reliable", "Complete 10 missions.",
                _event_count("mission_completed", 10)),
    Achievement("shepherd", "Shepherd", "Escort a trader safely to its destination.",
                _completed("Escort")),
    Achievement("headhunter", "Headhunter", "Collect a bounty.", _completed("Bounty")),
    Achievement("quiet_hands", "Quiet Hands", "Complete a smuggling run.",
                _completed("Smuggling")),
    Achievement("liberator", "Liberator", "Break a pirate stronghold.",
                _completed("Liberation")),
    Achievement("redrawn_map", "Redrawn Map", "Change who controls a region.",
                _events("region_flipped")),
    Achievement("caught", "Caught Red-Handed", "Have contraband seized by the Guild.",
                _events("contraband_seized")),
    Achievement("heir", "A Dead Man's Ship", "Finish the prologue.", _flag("prologue_complete")),
    Achievement("hollow", "The Hollow Account", "Uncover who pays the pirates.",
                _flag("act2_debriefed")),
    Achievement("signal", "The Signal", "Complete the campaign.", _flag("campaign_complete")),
    Achievement("every_road", "Every Road", "See all six endings.",
                lambda g: len(legacy.endings) >= 6),
    Achievement("second_time", "Second Time Around", "Complete the campaign twice.",
                lambda g: legacy.completions >= 2),
]

BY_ID = {a.id: a for a in ACHIEVEMENTS}


class Achievements:
    def __init__(self):
        self._since_check = CHECK_INTERVAL_SECONDS

    def is_unlocked(self, achievement_id: str) -> bool:
        legacy._ensure_loaded()
        return achievement_id in legacy.achievements

    def unlocked_count(self) -> int:
        legacy._ensure_loaded()
        return sum(1 for a in ACHIEVEMENTS if a.id in legacy.achievements)

    def check(self, game_engine) -> List[Achievement]:
        """Unlock every achievement whose condition now holds. Returns the
        ones newly unlocked."""
        legacy._ensure_loaded()
        newly = []
        for achievement in ACHIEVEMENTS:
            if achievement.id in legacy.achievements:
                continue
            try:
                met = achievement.condition(game_engine)
            except Exception:
                logger.exception(f"Achievement check failed: {achievement.id}")
                continue
            if met:
                newly.append(achievement)
        for achievement in newly:
            self._unlock(achievement)
        self._announce(newly)
        return newly

    def _announce(self, newly: List[Achievement]):
        """One message per unlock, but a pile of them (a veteran's first
        check after loading an old save) becomes a single summary, since the
        notification stack only holds a few."""
        from .ui.notifications import notifications
        color = (255, 215, 120)
        if len(newly) <= 2:
            for achievement in newly:
                notifications.push(f"Achievement unlocked: {achievement.name}", duration=6.0, color=color)
        else:
            notifications.push(f"{len(newly)} achievements unlocked - see the Logbook",
                               duration=8.0, color=color)

    def tick(self, delta_time: float, game_engine) -> List[Achievement]:
        """Throttled check for the main loop: conditions are cheap, but there
        is no reason to run them every frame."""
        self._since_check += delta_time
        if self._since_check < CHECK_INTERVAL_SECONDS:
            return []
        self._since_check = 0.0
        return self.check(game_engine)

    def _unlock(self, achievement: Achievement):
        legacy.unlock_achievement(achievement.id)

        try:
            from .steam.steam_manager import steam_manager
            steam_manager.unlock_achievement(achievement.id)
        except Exception:
            logger.exception("Steam achievement hook failed")


achievements = Achievements()
