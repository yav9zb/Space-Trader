"""New Game+: what carries over between playthroughs. Finishing the campaign
lets the player pick one legacy perk that is applied, once, to the next new
game. It lives in its own small file in the user data directory so it
survives new games and is never touched by save files.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from .paths import get_user_data_path

logger = logging.getLogger(__name__)

# id -> (name, description)
PERKS = {
    "veteran": ("Veteran's Name", "Start the next game with 15 reputation."),
    "old_money": ("Old Money", "Start the next game with 20% more credits."),
    "friends": ("Friends in Every Port", "Start with +10 standing with every faction."),
}

VETERAN_REPUTATION = 15
OLD_MONEY_FACTOR = 1.2
FRIENDS_STANDING = 10


class Legacy:
    def __init__(self, path: Optional[str] = None):
        self.path = path
        self.completions = 0
        self.endings = []
        self.pending_perk: Optional[str] = None
        self.loaded = False

    def _file(self) -> str:
        return self.path or get_user_data_path("legacy.json")

    # Persistence -------------------------------------------------------------

    def load(self):
        self.completions, self.endings, self.pending_perk = 0, [], None
        try:
            with open(self._file(), "r") as handle:
                data = json.load(handle)
            self.completions = int(data.get("completions", 0))
            self.endings = list(data.get("endings", []))
            perk = data.get("pending_perk")
            self.pending_perk = perk if perk in PERKS else None
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError):
            logger.exception("Could not read legacy file; starting without one")
        self.loaded = True

    def save(self):
        data: Dict[str, Any] = {
            "completions": self.completions,
            "endings": self.endings,
            "pending_perk": self.pending_perk,
        }
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self._file())), exist_ok=True)
            with open(self._file(), "w") as handle:
                json.dump(data, handle, indent=2)
        except OSError:
            logger.exception("Could not save legacy file")

    def _ensure_loaded(self):
        if not self.loaded:
            self.load()

    # Use ---------------------------------------------------------------------

    def record_completion(self, ending_title: str):
        self._ensure_loaded()
        self.completions += 1
        if ending_title not in self.endings:
            self.endings.append(ending_title)
        self.save()

    def choose_perk(self, perk_id: str):
        if perk_id not in PERKS:
            raise ValueError(f"Unknown legacy perk: {perk_id}")
        self._ensure_loaded()
        self.pending_perk = perk_id
        self.save()

    def apply_pending(self, game_engine) -> Optional[str]:
        """Apply the chosen perk to a freshly reset game, then use it up.
        Returns the perk id, or None if there was nothing to apply."""
        self._ensure_loaded()
        perk = self.pending_perk
        if perk is None:
            return None

        manager = game_engine.mission_manager
        if perk == "veteran":
            manager.reputation += VETERAN_REPUTATION
        elif perk == "old_money":
            game_engine.ship.credits = int(game_engine.ship.credits * OLD_MONEY_FACTOR)
        elif perk == "friends":
            for faction in manager.faction_standing:
                manager.faction_standing[faction] += FRIENDS_STANDING

        self.pending_perk = None
        self.save()
        return perk


legacy = Legacy()
