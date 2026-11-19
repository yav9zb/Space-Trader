"""Stage evaluators for story missions. A stage either measures a counter
against the value it had when the stage began (so earlier progress does not
count), or checks a live condition. Everything reads StoryState counters or
simple game state, so progress survives save/load without any per-kind
saved fields beyond the baselines.

`key` identifies a stage ("<story id>:<stage index>"); the fleet and escort
kinds use it to namespace the counters their spawned ships report through.
"""

from typing import Dict, List, Optional

from ..missions.rank_system import RANKS
from .chapters import Stage


def displayed_sector(position):
    """The sector as the Navigation HUD shows it (y is inverted)."""
    return int(position.x // 1000), int(-position.y // 1000)


def stage_counter(stage: Stage, resolved: Dict[str, str], key: str = "") -> Optional[str]:
    """Name of the StoryState counter a stage measures, if it uses one."""
    if stage.kind == "counter":
        return stage.params["counter"]
    if stage.kind == "dock_at":
        return f"docked_at:{resolved[stage.params['waypoint']]}"
    if stage.kind == "destroy_bandits":
        return "bandit_destroyed"
    if stage.kind == "fleet":
        return f"stronghold_killed:{key}"
    if stage.kind == "escort":
        return f"escort_arrived:{key}"
    return None


def stage_failure_counter(stage: Stage, key: str = "") -> Optional[str]:
    """A counter whose increase means the stage can no longer succeed."""
    if stage.kind == "escort":
        return f"escort_lost:{key}"
    return None


def stage_baseline_counters(stage: Stage, resolved: Dict[str, str], key: str = "") -> List[str]:
    """Every counter whose starting value must be remembered for this stage."""
    names = [stage_counter(stage, resolved, key), stage_failure_counter(stage, key)]
    return [name for name in names if name is not None]


def stage_needed(stage: Stage) -> int:
    if stage.kind == "fleet":
        return len(stage.params["ships"])
    if stage.kind in ("counter", "destroy_bandits"):
        return stage.params.get("count", 1)
    return 1


def is_stage_failed(stage: Stage, baselines: Dict[str, int], story, key: str = "") -> bool:
    counter = stage_failure_counter(stage, key)
    if counter is None:
        return False
    return story.count_events(counter) - baselines.get(counter, 0) >= 1


def is_stage_complete(stage: Stage, resolved: Dict[str, str], baselines: Dict[str, int],
                      ship, story, mission_manager, key: str = "") -> bool:
    counter = stage_counter(stage, resolved, key)
    if counter is not None:
        gained = story.count_events(counter) - baselines.get(counter, 0)
        return gained >= stage_needed(stage)

    if stage.kind == "earn_rank":
        return mission_manager.reputation >= dict(RANKS)[stage.params["rank"]]

    if stage.kind == "reach_sector":
        x, y = displayed_sector(ship.position)
        radius = stage.params.get("radius", 0)
        return (abs(x - stage.params["x"]) <= radius
                and abs(y - stage.params["y"]) <= radius)

    raise ValueError(f"Unknown stage kind: {stage.kind}")
