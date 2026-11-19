"""Starting a new game from the main menu must give a fresh ship."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from src.engine.game_engine import GameEngine


@pytest.fixture(scope="module")
def engine():
    return GameEngine()


@pytest.fixture(autouse=True)
def isolated_legacy(tmp_path, monkeypatch):
    """Never read or consume a developer's real legacy perk."""
    from src.legacy import legacy
    monkeypatch.setattr(legacy, "path", str(tmp_path / "legacy.json"))
    monkeypatch.setattr(legacy, "loaded", False)
    monkeypatch.setattr(legacy, "pending_perk", None)
    monkeypatch.setattr(legacy, "completions", 0)
    monkeypatch.setattr(legacy, "endings", [])
    monkeypatch.setattr(legacy, "achievements", [])


def test_a_new_game_does_not_keep_the_old_ships_wealth_or_upgrades(engine):
    ship = engine.ship
    ship.credits = 250_000
    ship.cargo_hold.add_cargo("food", 5)
    engine.mission_manager.reputation = 90
    held = engine.ship

    engine.create_new_universe()

    assert engine.ship is held                    # states keep their reference
    assert engine.ship.credits == 1000
    assert engine.ship.cargo_hold.items == {}
    assert engine.mission_manager.reputation == 0


def test_a_new_game_restarts_the_clock_and_forgets_the_outpost(engine):
    from src.story import outpost

    engine.create_new_universe()
    engine.play_time = 5000.0
    engine.story_state.npc_stations["act3_2.a"] = "Freeport-9"
    outpost.claim(engine, "Freeport-9")
    assert outpost.is_claimed(engine.story_state)

    engine.create_new_universe()

    assert engine.play_time == 0.0
    assert not outpost.is_claimed(engine.story_state)


def test_a_new_game_clears_ships_left_over_from_the_old_universe(engine):
    from pygame import Vector2
    from src.combat.combat_manager import combat_manager
    from src.entities.bandit import BanditShip, BanditType

    combat_manager.add_bandit(BanditShip(Vector2(50, 50), BanditType.FIGHTER))
    assert combat_manager.active_bandits

    engine.create_new_universe()

    assert combat_manager.active_bandits == []
    assert combat_manager.active_traders == []
    assert combat_manager.active_patrols == []


def test_the_ending_starts_victory_and_the_perk_applies_to_the_next_game(engine):
    from src.legacy import legacy
    from src.states.game_state import GameStates

    engine.create_new_universe()
    engine.story_state.set_flag("path_expose")
    engine.story_state.set_flag("signal_open")
    engine.story_state.set_flag("campaign_complete")

    engine.start_victory()
    assert "signal" in legacy.achievements        # unlocked at once, not on the next tick

    assert engine.current_state == GameStates.VICTORY
    assert engine.story_state.count_events("campaign_completed") == 1
    assert legacy.completions == 1 and legacy.endings == ["The Open Sky"]

    legacy.choose_perk("veteran")
    engine.create_new_universe()
    assert engine.mission_manager.reputation == 15
    assert legacy.pending_perk is None
    engine.change_state(GameStates.PLAYING)


def test_the_mission_tracker_does_not_sit_on_top_of_the_minimap(engine):
    """Both live in the top-right corner; with an active mission the tracker
    used to be drawn across the minimap."""
    import pygame
    from src.story import director
    from src.story.story_missions import start_story_mission
    from src.states.game_state import GameStates

    engine.create_new_universe()
    engine.story_state.chapter = "act_4"
    director.ensure_npcs_placed(engine)
    assert start_story_mission("act1_2", engine)

    class Clock:
        def get_time(self): return 16
        def tick(self, *a): return 16
        def get_fps(self): return 60.0
    real_clock = engine.clock
    engine.clock = Clock()
    try:
        engine.change_state(GameStates.PLAYING)
        engine.update()
        engine.render()
    finally:
        engine.clock = real_clock

    reserved = {a["name"]: a for a in engine.states[GameStates.PLAYING].enhanced_hud.ui_layout.reserved_areas}
    tracker = reserved["mission_tracker"]
    tracker_rect = pygame.Rect(tracker["x"], tracker["y"], tracker["width"], tracker["height"])
    minimap = engine.minimap
    minimap_rect = pygame.Rect(int(minimap.position.x), int(minimap.position.y),
                               minimap.map_size, minimap.map_size)
    assert not tracker_rect.colliderect(minimap_rect), (tracker_rect, minimap_rect)


def test_loading_an_old_prologue_save_puts_the_player_into_act_one_with_contacts(engine, tmp_path):
    """A save made by beta 9 to 12 after the prologue must continue into the
    new campaign, with the Act 1 contacts waiting at stations."""
    import json
    from src.save_system import SaveSystem

    engine.create_new_universe()
    system = SaveSystem(str(tmp_path))
    assert system.save_game(engine, "old")

    path = tmp_path / "old.json"
    data = json.loads(path.read_text())
    data["story"] = {
        "flags": {"prologue_complete": True, "prologue_epilogue_seen": True, "met_hale": True},
        "chapter": "prologue",
        "completed_story_missions": ["prologue_1", "prologue_2", "prologue_3"],
        "seen_nodes": ["hale_intro", "hale_epilogue"],
        "npc_stations": {"hale": engine.story_state.npc_stations["hale"]},
    }
    path.write_text(json.dumps(data))

    assert system.load_game("old", engine)

    assert engine.story_state.chapter == "act_1"
    for npc in ("rourke", "voss", "kestrel"):
        assert engine.story_state.npc_stations.get(npc), f"{npc} was not placed after loading"


def test_dying_keeps_active_story_missions_but_still_resets_ordinary_ones(engine):
    """Respawning wipes credits, upgrades and ordinary missions. Story
    missions are campaign progress: clearing them while StoryState still
    lists them as active would leave the contact unable to offer them again."""
    from src.missions.mission_types import Mission, MissionStatus
    from src.story import director
    from src.story.story_missions import start_story_mission
    from src.systems.respawn_system import respawn_system

    engine.create_new_universe()
    engine.story_state.chapter = "act_1"
    director.ensure_npcs_placed(engine)
    assert start_story_mission("act1_2", engine)
    ordinary = Mission()
    ordinary.status = MissionStatus.IN_PROGRESS
    engine.mission_manager.active_missions.append(ordinary)
    engine.ship.credits = 90_000

    respawn_system._reset_ship_to_safe_state(engine)

    assert engine.ship.credits == 1000                               # the usual penalty still applies
    assert ordinary not in engine.mission_manager.active_missions
    story_ids = [getattr(m, "story_id", None) for m in engine.mission_manager.active_missions]
    assert story_ids == ["act1_2"]
    assert engine.story_state.active_story_missions == ["act1_2"]    # and the two stay in agreement


def test_a_story_mission_can_still_be_finished_after_dying(engine):
    from src.story import director
    from src.story.story_missions import start_story_mission
    from src.systems.respawn_system import respawn_system

    engine.create_new_universe()
    engine.story_state.chapter = "act_1"
    director.ensure_npcs_placed(engine)
    start_story_mission("act1_2", engine)
    mission = next(m for m in engine.mission_manager.active_missions if m.story_id == "act1_2")

    respawn_system._reset_ship_to_safe_state(engine)

    engine.story_state.bump(f"docked_at:{mission.resolved['a']}")
    engine.mission_manager.update(engine)
    assert mission.stage_index == 1                                  # still progressing


def test_loading_a_save_stuck_by_the_old_death_bug_lets_the_contact_offer_the_mission_again(engine, tmp_path):
    """Saves made after dying mid-mission list the story mission as active with
    no mission behind it."""
    import json
    from src.save_system import SaveSystem
    from src.story import director
    from src.story.dialogue import DialogueSession
    from src.story.dialogue_data import NODES

    engine.create_new_universe()
    engine.story_state.chapter = "act_1"
    director.ensure_npcs_placed(engine)
    system = SaveSystem(str(tmp_path))
    assert system.save_game(engine, "stuck")

    path = tmp_path / "stuck.json"
    data = json.loads(path.read_text())
    data["story"]["active_story_missions"] = ["act1_2"]      # listed, but missions are empty
    data["missions"]["active_missions"] = []
    path.write_text(json.dumps(data))

    assert system.load_game("stuck", engine)

    assert engine.story_state.active_story_missions == []
    offered = [c.text for c in DialogueSession(NODES, "voss_intro", engine).visible_choices()]
    assert "What do you want from me?" in offered              # the offer is back
