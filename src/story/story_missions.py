"""StoryMission: a Mission driven by an authored definition (chapters.py).

It lives in the normal mission lists, so rewards, faction standing, saving,
and the Active tab all work as they do for generated missions. What is saved
is small (definition id, resolved station names, current stage, counter
baselines); the definition itself is looked up from data on load.
"""

from typing import Dict, Optional

from ..missions.mission_types import Mission, MissionType, MissionStatus, MissionObjective, \
    MissionPriority, MissionReward, MissionPenalty
from .chapters import STORY_MISSIONS, StoryMissionDef
from .objectives import (
    is_stage_complete, is_stage_failed, stage_baseline_counters, stage_needed,
    stage_destination,
)


class StoryMission(Mission):
    EXTRA_STATE_FIELDS = ("story_id", "resolved", "stage_index", "baselines", "spawned")

    def __init__(self, definition: StoryMissionDef, resolved: Dict[str, str],
                 mission_id: str = None):
        super().__init__(mission_id)
        self.story_id = definition.id
        self.resolved = dict(resolved)
        self.stage_index = 0
        self.baselines: Dict[str, int] = {}
        self.spawned = []          # stage indexes whose one-time spawns are done

        self.mission_type = MissionType.STORY
        self.priority = MissionPriority.HIGH
        self.title = definition.title
        self.description = definition.description.format(**self.resolved)
        self.reward = MissionReward(credits=definition.reward_credits,
                                    reputation_bonus=definition.reputation_bonus)
        self.penalty = MissionPenalty()
        self.objectives = [
            MissionObjective(description=stage.text.format(**self.resolved))
            for stage in definition.stages
        ]
        self.progress_description = self.objectives[0].description if self.objectives else ""

    @property
    def definition(self) -> StoryMissionDef:
        return STORY_MISSIONS[self.story_id]

    def begin(self, story):
        """Record where each counter stands now, so only progress made from
        here on counts toward the stage."""
        self._set_baseline(story)
        self._update_destination(story)

    def _update_destination(self, story):
        """Point the mission tracker at wherever the current stage happens."""
        stages = self.definition.stages
        if self.stage_index >= len(stages):
            return
        self.destination_station_id = stage_destination(
            stages[self.stage_index], self.resolved, story.npc_stations.get(self.definition.giver))

    def _stage_key(self, index=None) -> str:
        return f"{self.story_id}:{self.stage_index if index is None else index}"

    def _set_baseline(self, story):
        stages = self.definition.stages
        if self.stage_index < len(stages):
            stage = stages[self.stage_index]
            for counter in stage_baseline_counters(stage, self.resolved, self._stage_key()):
                self.baselines[counter] = story.count_events(counter)

    def evaluate(self, ship, story, mission_manager) -> bool:
        """Advance through every stage that is now satisfied. Returns True if
        the mission just completed."""
        if self.status not in (MissionStatus.ACCEPTED, MissionStatus.IN_PROGRESS):
            return False

        stages = self.definition.stages
        while self.stage_index < len(stages):
            stage = stages[self.stage_index]
            key = self._stage_key()
            if is_stage_failed(stage, self.baselines, story, key):
                self.status = MissionStatus.FAILED
                self.progress_description = "The trader was destroyed"
                return False
            if not is_stage_complete(stage, self.resolved, self.baselines, ship, story,
                                     mission_manager, key):
                break
            self.objectives[self.stage_index].completed = True
            self.stage_index += 1
            self._set_baseline(story)
            self._update_destination(story)

        self.completion_percentage = self.stage_index / len(stages)
        if self.stage_index >= len(stages):
            self.complete()
            return True

        self.progress_description = self.objectives[self.stage_index].description
        if self.stage_index > 0:
            self.status = MissionStatus.IN_PROGRESS
        return False

    # Spawning ----------------------------------------------------------------

    def on_update(self, game_engine):
        """Keep the current stage's ships in the world. Fleets and escorted
        traders are not saved, so after a load whatever is still owed (the
        survivors, or the trader) is spawned again."""
        # Remember the engine's manager (not saved) so rank checks use the
        # same reputation the player is actually earning
        self._mission_manager = game_engine.mission_manager
        if self.status not in (MissionStatus.ACCEPTED, MissionStatus.IN_PROGRESS):
            return
        stages = self.definition.stages
        if self.stage_index >= len(stages):
            return
        stage = stages[self.stage_index]
        if stage.kind == "fleet":
            self._ensure_fleet(stage, game_engine)
        elif stage.kind == "escort":
            self._ensure_escort(stage, game_engine)

    def _stage_position(self, stage, game_engine):
        """Where a fleet appears: beside a waypoint station, or the middle of
        a displayed sector."""
        from pygame import Vector2
        from .director import find_station_by_name

        if "at" in stage.params:
            station = find_station_by_name(self.resolved[stage.params["at"]],
                                           game_engine.universe)
            if station is None:
                return None
            return station.position + Vector2(station.size + 450, 0)
        x, y = stage.params["sector"]
        return Vector2(x * 1000 + 500, -(y * 1000 + 500))

    def _ensure_fleet(self, stage, game_engine):
        import math
        from pygame import Vector2
        from ..combat.combat_manager import combat_manager
        from ..entities.bandit import BanditShip, BanditType, BanditState
        from .story_state import story_state

        key = self._stage_key()
        counter = f"stronghold_killed:{key}"
        needed = stage_needed(stage)
        remaining = needed - (story_state.count_events(counter) - self.baselines.get(counter, 0))
        present = sum(1 for b in combat_manager.active_bandits
                      if b.stronghold_id == key and b.state != BanditState.DISABLED)
        missing = remaining - present
        if missing <= 0:
            return
        center = self._stage_position(stage, game_engine)
        if center is None:
            return
        ships = stage.params["ships"]
        for index, type_name in enumerate(ships[present:present + missing]):
            angle = 2 * math.pi * index / max(1, len(ships))
            ship = BanditShip(center + Vector2(math.cos(angle), math.sin(angle)) * 180,
                              BanditType(type_name))
            ship.stronghold_id = key
            if type_name == "boss" and stage.params.get("boss_name"):
                ship.name = stage.params["boss_name"]
            combat_manager.add_bandit(ship)
        self.status = MissionStatus.IN_PROGRESS

    def _ensure_escort(self, stage, game_engine):
        from pygame import Vector2
        from ..combat.combat_manager import combat_manager
        from ..entities.bandit import create_bandit_encounter
        from ..entities.trader import TraderShip
        from ..factions import get_station_faction
        from .director import find_station_by_name
        from .story_state import story_state

        key = self._stage_key()
        if (story_state.count_events(f"escort_arrived:{key}") - self.baselines.get(f"escort_arrived:{key}", 0)
                or story_state.count_events(f"escort_lost:{key}") - self.baselines.get(f"escort_lost:{key}", 0)):
            return  # settled; evaluate() resolves it

        origin_name = (game_engine.story_state.npc_stations.get(self.definition.giver)
                       if stage.params.get("from") in (None, "giver")
                       else self.resolved[stage.params["from"]])
        origin = find_station_by_name(origin_name, game_engine.universe) if origin_name else None
        destination = find_station_by_name(self.resolved[stage.params["to"]], game_engine.universe)
        if origin is None or destination is None:
            return

        if not any(t.escort_id == key and t.alive for t in combat_manager.active_traders):
            if self._stage_index_spawned("trader"):
                position = game_engine.ship.position + Vector2(80, 0)   # restored after a load
            else:
                position = origin.position + Vector2(origin.size + 40, 0)
            trader = TraderShip(position, destination,
                                get_station_faction(origin, game_engine.world_seed))
            trader.escort_id = key
            combat_manager.add_trader(trader)
            self._mark_spawned("trader")
            self.status = MissionStatus.IN_PROGRESS

        ambush = stage.params.get("ambush")
        if ambush and not self._stage_index_spawned("ambush"):
            route = destination.position - origin.position
            midpoint = (origin.position + destination.position) / 2
            if route.length() > 0:
                midpoint += Vector2(-route.y, route.x).normalize() * 250
            for bandit in create_bandit_encounter(midpoint, ambush):
                combat_manager.add_bandit(bandit)
            self._mark_spawned("ambush")

    def _stage_index_spawned(self, what: str) -> bool:
        return f"{self.stage_index}:{what}" in self.spawned

    def _mark_spawned(self, what: str):
        self.spawned.append(f"{self.stage_index}:{what}")

    def update_progress(self, ship, current_station=None) -> bool:
        from ..missions.mission_manager import mission_manager
        from .story_state import story_state
        manager = getattr(self, "_mission_manager", None) or mission_manager
        return self.evaluate(ship, story_state, manager)

    def run_completion_effects(self, game_engine):
        from .dialogue import apply_effects
        apply_effects(list(self.definition.on_complete), game_engine)


def create_story_mission(story_id: str, game_engine) -> Optional[StoryMission]:
    """Build a mission from its definition, resolving its waypoints to real
    stations. None if a waypoint could not be placed."""
    from .director import place_story_station

    definition = STORY_MISSIONS[story_id]
    story = game_engine.story_state

    resolved = {}
    for key, spec in definition.waypoints.items():
        station = place_story_station(f"{story_id}.{key}", spec, game_engine)
        if station is None:
            return None
        resolved[key] = station.name

    mission = StoryMission(definition, resolved)
    mission.origin_station_id = story.npc_stations.get(definition.giver)
    for stage, objective in zip(definition.stages, mission.objectives):
        if stage.kind == "dock_at":
            objective.target_station_id = resolved[stage.params["waypoint"]]
    return mission


def start_story_mission(story_id: str, game_engine) -> bool:
    """Create the mission and put it in the player's active list. Does nothing
    if it is already active or completed."""
    story = game_engine.story_state
    if story_id in story.active_story_missions or story_id in story.completed_story_missions:
        return False

    mission = create_story_mission(story_id, game_engine)
    if mission is None:
        return False
    mission.begin(story)
    if not game_engine.mission_manager.start_story_mission(mission, game_engine.ship):
        return False

    story.active_story_missions.append(story_id)
    story.record_event("story_mission_started", mission_id=story_id)
    return True
