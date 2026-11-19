import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pytest

import src.achievements as achievements_module
from src.achievements import ACHIEVEMENTS, BY_ID, Achievements, CHECK_INTERVAL_SECONDS
from src.legacy import Legacy
from src.missions.mission_manager import MissionManager
from src.missions.mission_types import Mission, MissionType, MissionStatus
from src.story.logbook import build_pages, TABS
from src.story.story_state import StoryState
from src.ui.notifications import notifications


@pytest.fixture
def fresh(tmp_path, monkeypatch):
    store = Legacy(path=str(tmp_path / "legacy.json"))
    store.load()
    monkeypatch.setattr(achievements_module, "legacy", store)
    notifications.clear()
    yield store
    notifications.clear()


def game(reputation=0, credits=0, flags=(), counters=None):
    story = StoryState()
    for flag in flags:
        story.set_flag(flag)
    for name, count in (counters or {}).items():
        story.bump(name, count)
    return SimpleNamespace(
        story_state=story,
        mission_manager=SimpleNamespace(reputation=reputation),
        ship=SimpleNamespace(credits=credits),
    )


# achievement id -> (a game that has just met the condition, a game that just misses it)
CASES = {
    "first_blood": (game(counters={"bandit_destroyed": 1}), game()),
    "pirate_bane": (game(counters={"bandit_destroyed": 25}), game(counters={"bandit_destroyed": 24})),
    "licensed": (game(reputation=15), game(reputation=14)),
    "captains_bars": (game(reputation=80), game(reputation=79)),
    "legend": (game(reputation=150), game(reputation=149)),
    "wealthy": (game(credits=50_000), game(credits=49_999)),
    "reliable": (game(counters={"mission_completed": 10}), game(counters={"mission_completed": 9})),
    "shepherd": (game(counters={"completed_type:Escort": 1}), game(counters={"completed_type:Bounty": 1})),
    "headhunter": (game(counters={"completed_type:Bounty": 1}), game(counters={"completed_type:Escort": 1})),
    "quiet_hands": (game(counters={"completed_type:Smuggling": 1}), game(counters={"completed_type:Delivery": 1})),
    "liberator": (game(counters={"completed_type:Liberation": 1}), game(counters={"completed_type:Bounty": 1})),
    "redrawn_map": (game(counters={"region_flipped": 1}), game()),
    "caught": (game(counters={"contraband_seized": 1}), game()),
    "home_port": (game(flags=["outpost_claimed"]), game(flags=["act2_debriefed"])),
    "heir": (game(flags=["prologue_complete"]), game(flags=["prologue_epilogue_seen"])),
    "hollow": (game(flags=["act2_debriefed"]), game(flags=["act1_debriefed"])),
    "signal": (game(flags=["campaign_complete"]), game(flags=["signal_open"])),
}


def test_every_achievement_has_a_case_or_is_a_legacy_one():
    legacy_based = {"every_road", "second_time"}
    assert set(CASES) | legacy_based == {a.id for a in ACHIEVEMENTS}


@pytest.mark.parametrize("achievement_id", CASES)
def test_an_achievement_unlocks_exactly_when_its_condition_is_met(achievement_id, fresh):
    met, missed = CASES[achievement_id]
    tracker = Achievements()

    assert achievement_id not in [a.id for a in tracker.check(missed)]
    assert achievement_id in [a.id for a in tracker.check(met)]


def test_legacy_based_achievements_need_every_ending_and_two_completions(fresh):
    tracker = Achievements()
    fresh.endings = ["a", "b", "c", "d", "e"]
    fresh.completions = 1
    got = {a.id for a in tracker.check(game())}
    assert "every_road" not in got and "second_time" not in got

    fresh.endings.append("f")
    fresh.completions = 2
    got = {a.id for a in tracker.check(game())}
    assert {"every_road", "second_time"} <= got


def test_an_unlock_is_announced_once_and_remembered(fresh):
    tracker = Achievements()
    met = game(counters={"bandit_destroyed": 1})

    first = tracker.check(met)
    assert [a.id for a in first] == ["first_blood"]
    assert any("First Blood" in item[0] for item in notifications.items)

    notifications.clear()
    assert tracker.check(met) == []
    assert notifications.items == []
    assert tracker.is_unlocked("first_blood") and tracker.unlocked_count() == 1


def test_unlocks_survive_a_restart_and_a_new_game(fresh):
    Achievements().check(game(reputation=15))
    reloaded = Legacy(path=fresh.path)
    reloaded.load()
    assert "licensed" in reloaded.achievements

    # a brand-new game has none of the conditions, but the unlock stays
    assert Achievements().check(game()) == []
    assert "licensed" in fresh.achievements


def test_unlocks_are_passed_to_steam(fresh, monkeypatch):
    from src.steam.steam_manager import steam_manager
    sent = []
    monkeypatch.setattr(steam_manager, "unlock_achievement", lambda a: sent.append(a) or True)
    Achievements().check(game(counters={"bandit_destroyed": 1}))
    assert sent == ["first_blood"]


def test_a_failing_steam_hook_never_breaks_the_game(fresh, monkeypatch):
    from src.steam.steam_manager import steam_manager

    def boom(_):
        raise RuntimeError("steam exploded")
    monkeypatch.setattr(steam_manager, "unlock_achievement", boom)
    got = Achievements().check(game(counters={"bandit_destroyed": 1}))
    assert [a.id for a in got] == ["first_blood"]


def test_a_broken_condition_is_skipped_not_fatal(fresh, monkeypatch):
    bad = achievements_module.Achievement("bad", "Bad", "x", lambda g: 1 / 0)
    monkeypatch.setattr(achievements_module, "ACHIEVEMENTS", [bad] + list(ACHIEVEMENTS))
    got = Achievements().check(game(counters={"bandit_destroyed": 1}))
    assert [a.id for a in got] == ["first_blood"]


def test_the_main_loop_check_is_throttled(fresh):
    tracker = Achievements()
    met = game(counters={"bandit_destroyed": 1})
    tracker._since_check = 0.0                            # as if it had just checked
    assert tracker.tick(0.016, met) == []                 # next frames: waiting
    assert tracker.tick(CHECK_INTERVAL_SECONDS - 0.5, met) == []
    assert [a.id for a in tracker.tick(1.0, met)] == ["first_blood"]


def test_completing_missions_counts_them_by_type():
    """The per-type counters the achievements read come from completions."""
    story = StoryState()
    import src.story.story_state as story_module
    manager = MissionManager()
    ship = SimpleNamespace(credits=0, cargo_hold=SimpleNamespace(add_cargo=lambda *a: None))
    mission = Mission()
    mission.mission_type = MissionType.ESCORT
    mission.status = MissionStatus.IN_PROGRESS
    manager.active_missions.append(mission)

    before = story_module.story_state.count_events("completed_type:Escort")
    manager.complete_mission(mission, ship, None)
    assert story_module.story_state.count_events("completed_type:Escort") == before + 1


def test_the_logbook_lists_every_achievement_and_marks_unlocked_ones(fresh):
    assert "Achievements" in TABS
    Achievements().check(game(reputation=15))
    page = build_pages(SimpleNamespace(
        universe=None, world_seed=1, story_state=StoryState(),
        mission_manager=SimpleNamespace(reputation=0, faction_standing={}),
        ship=SimpleNamespace(position=SimpleNamespace(x=0, y=0))))["Achievements"]
    text = [line for _, line in page]
    assert "1 of %d unlocked" % len(ACHIEVEMENTS) in text[0]
    assert "[x] Licensed" in text
    assert "[ ] First Blood" in text
    assert all(a.name in " ".join(text) for a in ACHIEVEMENTS)


def test_achievement_text_is_plain_ascii():
    for achievement in ACHIEVEMENTS:
        assert all(ord(ch) < 128 for ch in achievement.name + achievement.description)
    assert len({a.id for a in ACHIEVEMENTS}) == len(ACHIEVEMENTS) == len(BY_ID)


def test_a_pile_of_unlocks_becomes_one_summary_message(fresh):
    """A veteran loading an old save unlocks many at once; the notification
    stack only holds a few, so they are summarised rather than dropped."""
    veteran = game(reputation=150, credits=60_000, counters={"bandit_destroyed": 30},
                   flags=["prologue_complete"])
    got = Achievements().check(veteran)

    assert len(got) >= 5
    assert len(notifications.items) == 1
    assert f"{len(got)} achievements unlocked" in notifications.items[0][0]


def test_one_or_two_unlocks_are_named_individually(fresh):
    Achievements().check(game(counters={"bandit_destroyed": 1}))
    assert [i[0] for i in notifications.items] == ["Achievement unlocked: First Blood"]
