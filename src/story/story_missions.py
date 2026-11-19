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
from .objectives import is_stage_complete, stage_counter


class StoryMission(Mission):
    EXTRA_STATE_FIELDS = ("story_id", "resolved", "stage_index", "baselines")

    def __init__(self, definition: StoryMissionDef, resolved: Dict[str, str],
                 mission_id: str = None):
        super().__init__(mission_id)
        self.story_id = definition.id
        self.resolved = dict(resolved)
        self.stage_index = 0
        self.baselines: Dict[str, int] = {}

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

    def _set_baseline(self, story):
        stages = self.definition.stages
        if self.stage_index < len(stages):
            counter = stage_counter(stages[self.stage_index], self.resolved)
            if counter is not None:
                self.baselines[counter] = story.count_events(counter)

    def evaluate(self, ship, story, mission_manager) -> bool:
        """Advance through every stage that is now satisfied. Returns True if
        the mission just completed."""
        if self.status not in (MissionStatus.ACCEPTED, MissionStatus.IN_PROGRESS):
            return False

        stages = self.definition.stages
        while self.stage_index < len(stages):
            stage = stages[self.stage_index]
            if not is_stage_complete(stage, self.resolved, self.baselines, ship, story, mission_manager):
                break
            self.objectives[self.stage_index].completed = True
            self.stage_index += 1
            self._set_baseline(story)

        self.completion_percentage = self.stage_index / len(stages)
        if self.stage_index >= len(stages):
            self.complete()
            return True

        self.progress_description = self.objectives[self.stage_index].description
        if self.stage_index > 0:
            self.status = MissionStatus.IN_PROGRESS
        return False

    def update_progress(self, ship, current_station=None) -> bool:
        from ..missions.mission_manager import mission_manager
        from .story_state import story_state
        return self.evaluate(ship, story_state, mission_manager)

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
            mission.destination_station_id = mission.destination_station_id or objective.target_station_id
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
