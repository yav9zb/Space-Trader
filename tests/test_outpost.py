import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pytest

from src.entities.ship import Ship
from src.missions.mission_manager import MissionManager
from src.story import outpost
from src.story.dialogue import DialogueSession, apply_effects
from src.story.dialogue_data import NODES
from src.story.logbook import build_pages
from src.story.outpost import CAP, RATE_PER_MINUTE, COLLECTED_AT
from src.story.story_state import StoryState
from src.ui.notifications import notifications


@pytest.fixture
def engine():
    notifications.clear()
    story = StoryState()
    story.npc_stations["act3_2.a"] = "Freeport-9"
    eng = SimpleNamespace(story_state=story, ship=Ship(0, 0), play_time=1000.0,
                          mission_manager=MissionManager(), universe=None, world_seed=1)
    yield eng
    notifications.clear()


def station(name="Freeport-9"):
    return SimpleNamespace(name=name)


def claim(engine):
    apply_effects([{"type": "set_flag", "name": "outpost_claimed"},
                   {"type": "claim_outpost", "mission": "act3_2", "waypoint": "a"}], engine)


def test_claiming_makes_the_freed_station_the_outpost_and_starts_the_clock(engine):
    assert not outpost.is_claimed(engine.story_state)
    claim(engine)
    assert outpost.is_claimed(engine.story_state)
    assert engine.story_state.npc_stations["outpost"] == "Freeport-9"
    assert engine.story_state.get_flag(COLLECTED_AT) == 1000.0
    assert any("Outpost claimed" in item[0] for item in notifications.items)
    assert engine.story_state.count_events("outpost_claimed") == 1


def test_claiming_twice_or_without_a_station_does_nothing(engine):
    claim(engine)
    engine.play_time = 5000.0
    claim(engine)
    assert engine.story_state.get_flag(COLLECTED_AT) == 1000.0      # not restarted

    other = SimpleNamespace(story_state=StoryState(), ship=Ship(0, 0), play_time=0.0,
                            mission_manager=MissionManager())
    apply_effects([{"type": "claim_outpost", "mission": "act3_2", "waypoint": "a"}], other)
    assert not outpost.is_claimed(other.story_state)                # the waypoint was never placed


def test_income_accrues_by_the_minute_and_is_capped(engine):
    claim(engine)
    story = engine.story_state
    assert outpost.pending_income(story, 1000.0) == 0
    assert outpost.pending_income(story, 1000.0 + 60) == RATE_PER_MINUTE
    assert outpost.pending_income(story, 1000.0 + 600) == 10 * RATE_PER_MINUTE
    assert outpost.pending_income(story, 1000.0 + 10 ** 7) == CAP


def test_docking_at_the_outpost_pays_out_once_and_restarts_the_clock(engine):
    claim(engine)
    engine.play_time = 1000.0 + 600
    before = engine.ship.credits

    paid = outpost.collect(engine, station())
    assert paid == 10 * RATE_PER_MINUTE
    assert engine.ship.credits == before + paid
    assert any("Outpost income collected" in item[0] for item in notifications.items)

    assert outpost.collect(engine, station()) == 0                  # nothing new yet
    engine.play_time += 120
    assert outpost.collect(engine, station()) == 2 * RATE_PER_MINUTE


def test_other_stations_pay_nothing_and_do_not_reset_the_clock(engine):
    claim(engine)
    engine.play_time = 1000.0 + 600
    assert outpost.collect(engine, station("Somewhere-Else")) == 0
    assert engine.story_state.get_flag(COLLECTED_AT) == 1000.0
    assert outpost.collect(engine, station()) == 10 * RATE_PER_MINUTE


def test_nothing_is_paid_before_the_outpost_is_claimed(engine):
    engine.play_time = 10 ** 6
    assert outpost.collect(engine, station()) == 0
    assert outpost.pending_income(engine.story_state, engine.play_time) == 0


def test_loading_an_earlier_save_never_pays_for_negative_time(engine):
    claim(engine)
    assert outpost.pending_income(engine.story_state, 10.0) == 0
    engine.play_time = 10.0
    assert outpost.collect(engine, station()) == 0
    assert engine.story_state.get_flag(COLLECTED_AT) == 10.0        # the clock follows the rewound game


def test_the_outpost_survives_a_save_and_load(engine):
    claim(engine)
    blob = json.loads(json.dumps(engine.story_state.to_dict()))
    restored = StoryState()
    restored.from_dict(blob)
    assert outpost.is_claimed(restored)
    assert outpost.pending_income(restored, 1000.0 + 120) == 2 * RATE_PER_MINUTE


def test_hale_offers_the_station_only_after_the_warband_is_broken(engine):
    engine.story_state.chapter = "act_3"

    def offered():
        return [c.text for c in DialogueSession(NODES, "hale_return", engine).visible_choices()]

    assert "About the station we freed." not in offered()
    engine.story_state.completed_story_missions.append("act3_2")
    assert "About the station we freed." in offered()

    session = DialogueSession(NODES, "hale_outpost", engine)
    assert "Freeport-9" in session.current_text()
    session.choose([c.text for c in session.visible_choices()].index("I will claim it."))
    assert outpost.is_claimed(engine.story_state)
    assert "Freeport-9" in session.current_text()

    assert "About the station we freed." not in offered()
    assert "How is my outpost doing?" in offered()


def test_declining_leaves_the_offer_open(engine):
    engine.story_state.completed_story_missions.append("act3_2")
    session = DialogueSession(NODES, "hale_outpost", engine)
    session.choose([c.text for c in session.visible_choices()].index("Leave it for now."))
    assert not outpost.is_claimed(engine.story_state)
    assert "About the station we freed." in [
        c.text for c in DialogueSession(NODES, "hale_return", engine).visible_choices()]


def test_the_logbook_shows_the_outpost_and_what_is_waiting(engine):
    from src.universe import Universe
    universe = Universe(seed=5)
    universe.generate_universe()
    engine.universe, engine.world_seed = universe, universe.world_seed
    real = universe.stations[0]
    engine.story_state.npc_stations["act3_2.a"] = real.name
    engine.ship = SimpleNamespace(position=real.position)
    claim(engine)
    engine.play_time = 1000.0 + 300

    text = " ".join(t for _, t in build_pages(engine)["Story"])
    assert "Outpost" in text and real.name in text
    assert f"{5 * RATE_PER_MINUTE:,}" in text
