"""Stage evaluators for story missions. A stage either measures a counter
against the value it had when the stage began (so earlier progress does not
count), or checks a live condition. Everything reads StoryState counters or
simple game state, so progress survives save/load without any per-kind
saved fields beyond the baselines.
"""

from typing import Dict, Optional

from ..missions.rank_system import RANKS
from .chapters import Stage


def stage_counter(stage: Stage, resolved: Dict[str, str]) -> Optional[str]:
    """Name of the StoryState counter a stage measures, if it uses one."""
    if stage.kind == "counter":
        return stage.params["counter"]
    if stage.kind == "dock_at":
        return f"docked_at:{resolved[stage.params['waypoint']]}"
    if stage.kind == "destroy_bandits":
        return "bandit_destroyed"
    return None


def stage_needed(stage: Stage) -> int:
    if stage.kind in ("counter", "destroy_bandits"):
        return stage.params.get("count", 1)
    return 1


def is_stage_complete(stage: Stage, resolved: Dict[str, str], baselines: Dict[str, int],
                      ship, story, mission_manager) -> bool:
    counter = stage_counter(stage, resolved)
    if counter is not None:
        gained = story.count_events(counter) - baselines.get(counter, 0)
        return gained >= stage_needed(stage)

    if stage.kind == "earn_rank":
        return mission_manager.reputation >= dict(RANKS)[stage.params["rank"]]

    if stage.kind == "reach_sector":
        sector = (int(ship.position.x // 1000), int(ship.position.y // 1000))
        return sector == (stage.params["x"], stage.params["y"])

    raise ValueError(f"Unknown stage kind: {stage.kind}")
