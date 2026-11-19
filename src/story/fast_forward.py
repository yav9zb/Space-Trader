"""Jump a game to the start of a campaign act, for testing the later content
without playing through everything before it. Used by scripts/make_debug_save.py.

It does not invent state: it completes the earlier story missions, applies the
same effects their completions and conversations apply (ledger entries, flags,
chapter changes, the path choice with its standing and border changes), marks
the contacts as met, and places the stations they and the missions use.
"""

from typing import List

from .chapters import STORY_MISSIONS
from .dialogue import apply_effects
from .dialogue_data import NODES
from .director import ensure_npcs_placed, place_story_station
from .npcs import NPCS, chapter_index
from .story_missions import start_story_mission

STAGES = ["act1", "act2", "act3", "act4", "finale"]
PATHS = ["expose", "join", "independent"]

# Missions completed before each stage begins
_BEFORE = {
    "act1": ["prologue_1", "prologue_2", "prologue_3"],
    "act2": ["act1_1", "act1_2", "act1_3"],
    "act3": ["act2_1", "act2_2", "act2_3", "act2_4"],
    "act4": ["act3_1", "act3_2", "act3_3"],
    "finale": ["act4_1"],
}

# The conversation that closes each stretch of the story
_DEBRIEF = {"act1": "hale_epilogue", "act2": "hale_act1_end", "act3": "hale_act2_end"}

_REPUTATION = {"act1": 20, "act2": 45, "act3": 85, "act4": 100, "finale": 120}
_CREDITS = {"act1": 3000, "act2": 12000, "act3": 40000, "act4": 80000, "finale": 100000}

_PATH_NODE = {"expose": "hale_after_expose", "join": "hale_after_join",
              "independent": "hale_after_independent"}


def _complete(engine, mission_id: str):
    """Mark a story mission done, with the world state it would have left."""
    definition = STORY_MISSIONS[mission_id]
    story = engine.story_state
    for key, spec in definition.waypoints.items():
        place_story_station(f"{mission_id}.{key}", spec, engine)
    if mission_id not in story.completed_story_missions:
        story.completed_story_missions.append(mission_id)
    # Its scenes and follow-on missions are the player's to trigger, not ours
    effects = [e for e in definition.on_complete
               if e["type"] not in ("show_dialogue", "start_story_mission")]
    apply_effects(effects, engine)


def _meet_contacts(engine):
    """Introduce every contact whose act has been played, i.e. whose chapter
    comes before the one the story is now in. Contacts of the current act
    have not been met yet."""
    story = engine.story_state
    for npc in NPCS.values():
        if chapter_index(npc.chapter) < chapter_index(story.chapter):
            apply_effects(NODES[npc.intro_node].on_enter, engine)
            story.mark_node_seen(npc.intro_node)


def _choose_path(engine, path: str):
    for choice in NODES["hale_choice"].choices:
        if choice.next == _PATH_NODE[path]:
            apply_effects(choice.effects, engine)
            return
    raise ValueError(path)


def fast_forward(engine, stage: str, path: str = "independent") -> List[str]:
    """Bring a new game to the start of `stage`. Stages from act4 on come
    after the Act 3 choice, which is made on the given path; "act3" itself
    starts just before the choice. Returns the story missions completed on
    the way."""
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    if path not in PATHS:
        raise ValueError(f"path must be one of {PATHS}")

    story = engine.story_state
    wanted = STAGES.index(stage)
    story.mark_node_seen("hale_intro")
    apply_effects(NODES["hale_friend"].on_enter, engine)          # the ledger cover
    apply_effects([{"type": "set_flag", "name": "met_hale"}], engine)
    done: List[str] = []

    for name in STAGES[: wanted + 1]:
        if name == "act4":
            _choose_path(engine, path)                            # made at the start of Act 3
            story.mark_node_seen("hale_choice")
        for mission_id in _BEFORE[name]:
            _complete(engine, mission_id)
            done.append(mission_id)
        if name in _DEBRIEF:
            apply_effects(NODES[_DEBRIEF[name]].on_enter, engine)  # flags and the next chapter
            story.mark_node_seen(_DEBRIEF[name])

    _meet_contacts(engine)
    if stage == "finale":
        start_story_mission("act4_2", engine)

    engine.mission_manager.reputation = _REPUTATION[stage]
    engine.ship.credits = _CREDITS[stage]
    ensure_npcs_placed(engine)
    return done
