"""Plays the whole campaign, prologue to ending, through the real dialogue
and mission systems for each of the three paths. Game events (docking,
kills, arrivals) are produced the way the game produces them; only the
flying is skipped. A broken gate, token, counter or hand-off anywhere in the
authored data shows up here as a conversation choice that is not offered or a
mission that never completes."""

import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pytest
from pygame import Vector2

from src.combat.combat_manager import combat_manager
from src.entities.ship import Ship
from src.factions import FACTION_PIRATE, get_controlling_faction
from src.missions.mission_manager import MissionManager
from src.story import director
from src.story.chapters_acts import SIGNAL_SECTOR
from src.story.dialogue import DialogueSession
from src.story.dialogue_data import NODES
from src.story.npcs import NPCS
from src.story.story_state import story_state
from src.universe import Universe


class Campaign:
    """Drives a SimpleNamespace engine the way a player would."""

    def __init__(self):
        story_state.reset()
        for group in (combat_manager.active_bandits, combat_manager.active_traders,
                      combat_manager.active_patrols):
            group.clear()
        universe = Universe(seed=9001)
        universe.generate_universe()
        self.engine = SimpleNamespace(
            universe=universe, world_seed=universe.world_seed, story_state=story_state,
            mission_manager=MissionManager(), ship=Ship(0, 0), play_time=0.0,
            opened=[], victory=0,
        )
        self.engine.start_dialogue = self.engine.opened.append
        self.engine.start_victory = lambda: setattr(self.engine, "victory", self.engine.victory + 1)
        director.ensure_npcs_placed(self.engine)

    # Conversation -----------------------------------------------------------------

    def talk(self, npc_id, *picks):
        """Open the contact's conversation and pick the given choices in order."""
        npc = NPCS[npc_id]
        assert story_state.npc_stations.get(npc_id), f"{npc_id} has not been placed yet"
        self.play(director.start_node_for(npc, story_state), *picks)

    def play(self, node_id, *picks):
        session = DialogueSession(NODES, node_id, self.engine)
        for text in picks:
            offered = [c.text for c in session.visible_choices()]
            assert text in offered, f"'{text}' not offered at {session.current.id}; offered: {offered}"
            session.choose(offered.index(text))
        return session

    def play_next_scene(self, *picks):
        """Play the scene a mission completion queued up."""
        assert self.engine.opened, "no scene was queued"
        return self.play(self.engine.opened.pop(0), *picks)

    # World events -----------------------------------------------------------------

    def update(self, times=2):
        for _ in range(times):
            self.engine.mission_manager.update(self.engine)

    def mission(self, story_id):
        return next(m for m in self.engine.mission_manager.active_missions
                    if getattr(m, "story_id", None) == story_id)

    def dock(self, story_id, waypoint):
        mission = self.mission(story_id)
        story_state.bump(f"docked_at:{mission.resolved[waypoint]}")
        self.update()

    def kill_bandits(self, count):
        for _ in range(count):
            story_state.bump("bandit_destroyed")
        self.update()

    def break_fleet(self, story_id, stage=0):
        key = f"{story_id}:{stage}"
        self.update()                                  # the fleet spawns
        ships = [b for b in combat_manager.active_bandits if b.stronghold_id == key]
        assert ships, f"no fleet spawned for {key}"
        for ship in ships:
            combat_manager._handle_bandit_destroyed(ship, self.engine.ship)
        self.update()

    def escort_arrives(self, story_id):
        self.update()                                  # trader and ambush spawn
        key = f"{story_id}:0"
        trader = next(t for t in combat_manager.active_traders if t.escort_id == key)
        trader.position = Vector2(trader.destination_station.position)
        trader.update(0.1, self.engine)
        self.update()

    def done(self, story_id):
        return story_id in story_state.completed_story_missions

    # Save / load -----------------------------------------------------------------------

    def save_and_reload(self):
        blob = json.loads(json.dumps({
            "story": story_state.to_dict(),
            "missions": self.engine.mission_manager.to_dict(),
        }))
        story_state.from_dict(blob["story"])
        self.engine.mission_manager.from_dict(blob["missions"])
        for group in (combat_manager.active_bandits, combat_manager.active_traders):
            group.clear()                              # runtime ships are not saved


def prologue(c):
    c.talk("hale", "Jessup Vane was your friend?", "What is in the ledger?",
           "I will earn that license.")
    c.engine.mission_manager.reputation = 15
    c.update()
    c.talk("hale", "I have earned my trader's license.", "I will look into it.")
    c.dock("prologue_2", "a")
    assert c.done("prologue_2")
    c.engine.opened.clear()
    c.talk("hale", "I found Vane's locker.", "I will be careful.")
    c.dock("prologue_3", "b")
    assert c.done("prologue_3")
    c.engine.opened.clear()
    c.talk("hale", "I met the courier.", "I will hear them out.")
    assert story_state.chapter == "act_1"


def act1(c):
    c.talk("rourke", "What do you need?", "I will do it.", "On my way.")
    c.escort_arrives("act1_1")
    assert c.done("act1_1")
    c.play_next_scene("Thank you, Rourke.")

    c.talk("voss", "What do you want from me?", "I will collect them.", "On my way.")
    c.dock("act1_2", "a")
    c.talk("voss", "I have the manifests.", "I will tell him.")
    c.update()
    assert c.done("act1_2")

    c.talk("kestrel", "What do you want?", "Six raiders. Done.", "I will be back.")
    c.kill_bandits(6)
    c.talk("kestrel", "The lanes are clear now.", "Thank you, Kestrel.")
    c.update()
    assert c.done("act1_3")

    c.talk("hale", "Rourke, Voss and Kestrel have each told me their part.", "I will find him.")
    assert story_state.chapter == "act_2"


def act2(c):
    c.talk("archivist", "What can you tell me now?", "I will fetch the case.", "Understood.")
    c.dock("act2_1", "a")
    c.talk("archivist", "I have the copied ledgers.", "Thank you. I will use it.")
    c.update()
    assert c.done("act2_1")

    c.talk("kestrel", "Tell me about the Hollow Account.", "I will take him.", "Consider him dead.")
    c.break_fleet("act2_2")
    c.talk("kestrel", "I have Dross's receipts.", "They will believe it now.")
    c.update()
    assert c.done("act2_2")

    c.talk("rourke", "You said a witness might talk.", "I will get him there.", "Understood.")
    c.escort_arrives("act2_3")
    assert c.done("act2_3")
    c.play_next_scene("It will not be wasted.")

    c.talk("voss", "Marrow's people want to meet me.", "I will go.", "Understood.")
    c.dock("act2_4", "a")
    c.talk("voss", "I met Marrow's man.", "I will choose carefully.")
    c.update()
    assert c.done("act2_4")

    c.talk("hale", "I have the ledgers, the receipts and a witness.",
           "What should I do with the evidence?")
    assert story_state.chapter == "act_3"


def act3(c, path_choice):
    c.play("hale_choice", path_choice)
    c.update()
    assert c.done("act3_1")

    c.talk("hale", "The frontier is in chaos.", "I will deal with it.")
    c.break_fleet("act3_2")
    assert c.done("act3_2")

    c.talk("hale", "About the station we freed.", "I will claim it.", "Thank you, Hale.")
    assert story_state.npc_stations["outpost"] == story_state.npc_stations["act3_2.a"]

    c.talk("okoye", "What do you need?", "I will calibrate the array.", "On my way.")
    c.dock("act3_3", "a")
    c.talk("okoye", "The array is calibrated.", "Then we go there.")
    c.update()
    assert c.done("act3_3")
    assert story_state.chapter == "act_4"


def act4(c, final_choice):
    c.talk("okoye", "What did the decoded page say?", "I will earn it.")
    c.engine.mission_manager.reputation = 80
    c.update()
    c.talk("okoye", "I have earned my captain's rank.", "Give it to me.", "I will find it.")
    c.update()
    assert c.done("act4_1")

    signal(c, final_choice)


def signal(c, final_choice):
    """From having the coordinates to the ending."""
    c.engine.ship.position = Vector2(SIGNAL_SECTOR[0] * 1000 + 500, -(SIGNAL_SECTOR[1] * 1000 + 500))
    c.update()
    assert c.done("act4_2")
    c.engine.opened.clear()                            # the arrival scene

    c.break_fleet("act4_3")
    assert c.done("act4_3")
    c.play_next_scene(final_choice)


PATHS = {
    "expose": ("Expose the Hollow Account.", "path_expose"),
    "join": ("Accept Marrow's offer.", "path_join"),
    "independent": ("Broker a truce and keep the lanes free.", "path_independent"),
}


@pytest.mark.parametrize("path", PATHS)
def test_the_whole_campaign_is_playable_on_every_path(path):
    choice, flag = PATHS[path]
    c = Campaign()
    prologue(c)
    act1(c)
    act2(c)
    act3(c, choice)
    act4(c, "Open the Signal to every faction.")

    assert story_state.has_flag(flag)
    assert story_state.has_flag("signal_open") and story_state.has_flag("campaign_complete")
    assert c.engine.victory == 1
    assert set(story_state.completed_story_missions) == {
        "prologue_1", "prologue_2", "prologue_3",
        "act1_1", "act1_2", "act1_3", "act2_1", "act2_2", "act2_3", "act2_4",
        "act3_1", "act3_2", "act3_3", "act4_1", "act4_2", "act4_3",
    }
    assert story_state.active_story_missions == []


def test_sealing_the_signal_also_ends_the_campaign():
    c = Campaign()
    prologue(c); act1(c); act2(c)
    act3(c, PATHS["expose"][0])
    act4(c, "Seal it until we understand it.")
    assert story_state.has_flag("signal_sealed") and not story_state.has_flag("signal_open")
    assert c.engine.victory == 1


def test_the_path_choice_changes_the_borders_and_standing():
    results = {}
    for path, (choice, _) in PATHS.items():
        c = Campaign()
        prologue(c); act1(c); act2(c)
        c.play("hale_choice", choice)
        results[path] = (
            dict(c.engine.mission_manager.faction_standing),
            dict(story_state.region_overrides),
        )
    expose, join, independent = (results[p] for p in ("expose", "join", "independent"))
    assert expose[0]["Trade Guild"] < 0 < join[0]["Trade Guild"]
    assert independent[0]["Independent"] > join[0]["Independent"]
    assert set(expose[1].values()) == {"Independent"}
    assert "Trade Guild" in join[1].values()
    assert set(independent[1].values()) == {"Independent"}
    assert len(expose[1]) > len(independent[1])         # exposing breaks both blocs


def test_the_campaign_survives_a_save_and_load_at_every_act_boundary():
    c = Campaign()
    prologue(c); c.save_and_reload()
    act1(c); c.save_and_reload()
    act2(c); c.save_and_reload()
    act3(c, PATHS["join"][0]); c.save_and_reload()
    act4(c, "Open the Signal to every faction.")
    assert c.engine.victory == 1


def test_a_fleet_and_an_escort_survive_a_reload_mid_mission():
    c = Campaign()
    prologue(c)
    act1(c)
    c.talk("archivist", "What can you tell me now?", "I will fetch the case.", "Understood.")
    c.dock("act2_1", "a")
    c.talk("archivist", "I have the copied ledgers.", "Thank you. I will use it.")
    c.update()
    c.talk("kestrel", "Tell me about the Hollow Account.", "I will take him.", "Consider him dead.")
    c.update()
    assert any(b.stronghold_id == "act2_2:0" for b in combat_manager.active_bandits)
    c.save_and_reload()
    c.update()
    assert sum(1 for b in combat_manager.active_bandits if b.stronghold_id == "act2_2:0") == 4
    c.break_fleet("act2_2")
    c.talk("kestrel", "I have Dross's receipts.", "They will believe it now.")
    c.update()
    assert c.done("act2_2")


def test_the_mission_tracker_points_at_wherever_the_current_stage_happens():
    c = Campaign()
    prologue(c)

    c.talk("rourke", "What do you need?", "I will do it.", "On my way.")
    freighter = c.mission("act1_1")
    assert freighter.destination_station_id == freighter.resolved["b"]       # escort: where it is going
    c.escort_arrives("act1_1")
    c.engine.opened.clear()

    c.talk("voss", "What do you want from me?", "I will collect them.", "On my way.")
    manifests = c.mission("act1_2")
    voss_station = story_state.npc_stations["voss"]
    assert manifests.destination_station_id == manifests.resolved["a"]       # first, the annex
    c.dock("act1_2", "a")
    assert manifests.destination_station_id == voss_station                  # then back to Voss

    c.talk("voss", "I have the manifests.", "I will tell him.")
    c.update()
    c.talk("kestrel", "What do you want?", "Six raiders. Done.", "I will be back.")
    assert c.mission("act1_3").destination_station_id is None                # bandits: no place
    c.kill_bandits(6)
    assert c.mission("act1_3").destination_station_id == story_state.npc_stations["kestrel"]


def test_fleet_and_sector_stages_show_where_to_go_and_it_survives_a_reload():
    c = Campaign()
    c.engine.mission_manager.reputation = 200
    story_state.chapter = "act_4"
    director.ensure_npcs_placed(c.engine)
    from src.story.story_missions import start_story_mission

    assert start_story_mission("act2_2", c.engine)
    fleet = c.mission("act2_2")
    assert fleet.destination_station_id == fleet.resolved["a"]               # the paymaster's station
    c.update()
    c.save_and_reload()
    assert c.mission("act2_2").destination_station_id == fleet.resolved["a"]

    assert start_story_mission("act4_2", c.engine)
    assert c.mission("act4_2").destination_station_id == "Sector (%d, %d)" % SIGNAL_SECTOR


def test_hale_can_say_where_the_three_contacts_are_until_act_one_is_done():
    c = Campaign()
    prologue(c)
    session = c.play("hale_return", "Where can I find them again?")
    text = session.current_text()
    for npc in ("rourke", "voss", "kestrel"):
        assert story_state.npc_stations[npc] in text

    # not offered before the epilogue, nor once Act 1 is wrapped up
    story_state.flags.pop("prologue_epilogue_seen")
    offered = [x.text for x in DialogueSession(NODES, "hale_return", c.engine).visible_choices()]
    assert "Where can I find them again?" not in offered
    story_state.set_flag("prologue_epilogue_seen")
    story_state.set_flag("act1_debriefed")
    offered = [x.text for x in DialogueSession(NODES, "hale_return", c.engine).visible_choices()]
    assert "Where can I find them again?" not in offered
