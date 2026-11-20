"""Base defense: turrets that shoot, modules that can be knocked out and mend, and
raids - real ships when the player is near, settled by numbers when they are away."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random

import pytest
from pygame import Vector2

from src.base_building import base_entity as be
from src.base_building import raids
from src.base_building.base_entity import BUILDABLE, BaseModule, ModuleType, PlayerBase
from src.base_building.base_manager import BaseManager
from src.combat.combat_manager import CombatManager
from src.entities.bandit import BanditShip, BanditState, BanditType


class Wallet:
    def __init__(self, credits=0):
        self.credits = credits


def built(base, steps=200, dt=1.0):
    for _ in range(steps):
        base.update(dt)


def make_base(turrets=0, extra_modules=1):
    """A base with power, storage, goods in it, and `turrets` turrets (all built)."""
    base = PlayerBase(0, 0, "Test")
    base.add_module(ModuleType.POWER_GENERATOR, 3, 0, free=True)
    base.add_module(ModuleType.STORAGE, 4, 0, free=True)
    for i in range(turrets):
        base.add_module(ModuleType.TURRET, -4 + i, -4, free=True)
    for i in range(extra_modules - 1):
        base.add_module(ModuleType.STORAGE, 4 + i + 1, 0, free=True)
    built(base)
    base.add_resource("metal_ore", 20)
    base.add_resource("machinery", 10)
    return base


def bandit_at(x, y, kind=BanditType.SCOUT):
    bandit = BanditShip(Vector2(x, y), kind)
    return bandit


def turret_of(base):
    return base.turrets()[0]


# --- the turret module -------------------------------------------------------------------------

def test_the_turret_is_a_buildable_module_with_a_weapon_a_price_and_a_power_draw():
    assert ModuleType.TURRET in BUILDABLE
    stats = BaseModule.MODULE_DEFINITIONS[ModuleType.TURRET]
    assert stats.weapon and stats.power_consumption > 0 and stats.cost_credits > 0 and stats.build_time > 0
    assert BaseModule(ModuleType.TURRET, 0, 0).is_turret
    assert not BaseModule(ModuleType.STORAGE, 0, 0).is_turret


def test_a_turret_shoots_a_raider_in_range_and_destroys_it():
    base = make_base(turrets=1)
    scout = bandit_at(500, 0)
    kills = 0
    for frame in range(600):
        base.update(1 / 30)
        for projectile, target in base.defend([scout], now=frame / 30):
            if target.take_damage(projectile.damage):
                kills += 1
        if scout.state == BanditState.DISABLED:
            break
    assert scout.state == BanditState.DISABLED and kills == 1


def test_a_turret_leads_a_moving_target():
    base = make_base(turrets=1)
    mover = bandit_at(600, 0)
    mover.velocity = Vector2(0, 400)
    still = bandit_at(600, 0)
    base.update(0.1)
    base.defend([still], now=5.0)
    flat = Vector2(turret_of(base).aim)
    base.defend([mover], now=10.0)
    assert turret_of(base).aim.y > flat.y + 0.05


def test_a_turret_leaves_a_target_out_of_range_alone():
    base = make_base(turrets=1)
    far = bandit_at(be.TURRET_RANGE + 600, 0)
    base.update(0.1)
    assert base.defend([far], now=10.0) == []
    assert turret_of(base).weapon_system.projectiles == []


def test_a_turret_that_is_still_being_built_does_not_fire():
    base = PlayerBase(0, 0, "Test")
    base.add_module(ModuleType.POWER_GENERATOR, 3, 0, free=True)
    base.add_module(ModuleType.TURRET, -3, 0, free=True)
    base.update(1.0)
    base.defend([bandit_at(300, 0)], now=5.0)
    assert turret_of(base).weapon_system.projectiles == []
    assert base.defense_rating() == 0


def test_a_turret_needs_power_to_fire():
    base = PlayerBase(0, 0, "Test")                    # the core gives 60 power; a turret wants 25
    for i in range(4):                                  # four turrets want 100, with only 60 + 20 spare
        base.add_module(ModuleType.TURRET, -3 + i, -4, free=True)
    built(base)
    assert base.power_ratio < 1.0
    # Nothing is wrong at 4 turrets with a ratio of 0.6, but starve it and they go quiet
    for i in range(4):
        base.add_module(ModuleType.TURRET, -3 + i, -3, free=True)
    built(base)
    assert base.power_ratio < be.TURRET_MIN_POWER
    base.defend([bandit_at(300, 0)], now=5.0)
    assert all(t.weapon_system.projectiles == [] for t in base.turrets())
    assert base.defense_rating() == 0


def test_defense_rating_counts_working_turrets():
    assert make_base(turrets=0).defense_rating() == 0
    assert make_base(turrets=2).defense_rating() == 2 * be.TURRET_DEFENSE


def test_turret_shots_are_drawn_as_friendly_fire():
    base = make_base(turrets=1)
    base.update(0.1)
    base.defend([bandit_at(300, 0)], now=5.0)
    projectile = turret_of(base).weapon_system.projectiles[0]
    assert projectile._palette()[0] == (70, 220, 120)


# --- damage and mending --------------------------------------------------------------------------

def test_a_module_is_knocked_out_at_no_hull_and_stops_working():
    base = make_base()
    storage = base.modules[(4, 0)]
    before = base.storage_capacity
    assert storage.take_damage(storage.stats.max_hull) is True
    base.update(0.0)
    assert storage.wrecked and not storage.is_operational
    assert base.storage_capacity == before - storage.stats.storage_capacity
    assert storage.take_damage(10) is False                    # already out: not a new knock-out


def test_a_knocked_out_generator_stops_powering_the_base():
    base = make_base()
    generator = base.modules[(3, 0)]
    before = base.power_generation
    generator.take_damage(generator.stats.max_hull)
    base.update(0.0)
    assert base.power_generation == before - generator.stats.power_generation


def test_damaged_modules_mend_and_come_back_when_half_mended():
    base = make_base()
    storage = base.modules[(4, 0)]
    storage.take_damage(storage.stats.max_hull)
    base.update(0.0)
    needed = storage.stats.max_hull * be.RESTORE_AT / (storage.stats.max_hull * be.REPAIR_RATE)
    base.update(needed * 0.5)
    assert storage.wrecked
    base.update(needed * 0.6)
    assert not storage.wrecked and storage.is_operational
    base.update(1000)
    assert storage.hull == storage.stats.max_hull


def test_nothing_mends_while_a_raid_is_on():
    base = make_base()
    storage = base.modules[(4, 0)]
    storage.take_damage(100)
    hurt = storage.hull
    base.under_attack = True
    base.update(60.0)
    assert storage.hull == hurt
    base.under_attack = False
    base.update(60.0)
    assert storage.hull > hurt


def test_the_command_center_has_the_most_hull():
    hulls = {t: BaseModule.MODULE_DEFINITIONS[t].max_hull for t in ModuleType}
    assert hulls[ModuleType.COMMAND_CENTER] == max(hulls.values())


def test_a_raiders_shot_that_hits_a_module_damages_it():
    base = make_base()
    targets = base.hit_targets()
    storage = base.modules[(4, 0)]
    target = next(t for t in targets if t.module is storage)
    assert (target.position - storage.get_world_position(base.position, base.grid_size)).length() == 0
    assert target.size > 0
    target.take_damage(40)
    assert storage.hull == storage.stats.max_hull - 40


def test_only_finished_modules_are_hit():
    base = PlayerBase(0, 0, "Test")
    base.add_module(ModuleType.STORAGE, 3, 0, free=True)       # not built yet
    assert {t.module.module_type for t in base.hit_targets()} == {ModuleType.COMMAND_CENTER}


# --- the raid level ---------------------------------------------------------------------------------

def test_a_base_with_only_its_command_center_is_not_worth_raiding():
    assert not raids.is_worth_raiding(PlayerBase(0, 0, "Bare"))
    assert raids.is_worth_raiding(make_base())


def test_bigger_bases_draw_bigger_raids_up_to_a_limit():
    levels = [raids.raid_level(make_base(extra_modules=n)) for n in range(1, 4)]
    assert levels == sorted(levels)
    threats = [raids.threat_of(raids.raid_roster(level)) for level in range(1, raids.MAX_LEVEL + 1)]
    assert threats == sorted(threats) and len(set(threats)) == len(threats)
    big = PlayerBase(0, 0, "Big")
    for i in range(16):
        big.add_module(ModuleType.STORAGE, -9 + i % 8, 5 + i // 8, free=True)
    built(big)
    assert raids.raid_level(big) == raids.MAX_LEVEL


def test_the_turrets_it_takes_to_stand_against_each_level_are_affordable_in_turns():
    # The top raid asks for a handful of turrets, not a hundred
    top = raids.threat_of(raids.raid_roster(raids.MAX_LEVEL))
    assert 3 <= top / be.TURRET_DEFENSE <= 6


# --- the director ---------------------------------------------------------------------------------------

@pytest.fixture
def world():
    manager = BaseManager()
    manager.raids.rng = random.Random(7)
    combat = CombatManager()
    return manager, combat


def add(manager, base, base_id="base_1"):
    manager.bases[base_id] = base
    return base_id


def run(manager, combat, seconds, player=Vector2(0, 0), step=1.0):
    t = 0.0
    while t < seconds:
        manager.raids.update(step, manager.bases, player, combat)
        t += step


def test_a_bare_base_is_never_raided(world):
    manager, combat = world
    add(manager, PlayerBase(0, 0, "Bare"))
    run(manager, combat, 5000)
    assert manager.events == [] and combat.active_bandits == []


def test_the_first_raid_comes_after_a_wait_not_at_once(world):
    manager, combat = world
    add(manager, make_base())
    run(manager, combat, raids.RAID_INTERVAL[0] - 10)
    assert manager.events == [] and combat.active_bandits == []
    run(manager, combat, raids.RAID_INTERVAL[1])
    assert manager.events                                         # something has happened by now


def test_a_raid_with_the_player_near_sends_real_ships_that_attack_the_base(world):
    manager, combat = world
    base = make_base(turrets=0)
    add(manager, base)
    manager.raids.launch("base_1", base, Vector2(500, 0), combat)
    assert combat.active_bandits
    assert all(b.raid_base is base for b in combat.active_bandits)
    assert all((b.position - base.position).length() > raids.SPAWN_DISTANCE - 400 for b in combat.active_bandits)
    assert base.under_attack
    assert any("attacking" in text for text, _ in manager.events)


def test_a_big_raid_on_a_poorly_defended_base_knocks_modules_out(world):
    manager, combat = world
    base = make_base(turrets=0, extra_modules=8)
    add(manager, base)
    assert raids.raid_level(base) >= 4
    manager.raids.launch("base_1", base, Vector2(50000, 0), combat)
    assert base.wrecked_count() >= 1


def test_a_raid_with_the_player_away_is_settled_without_ships(world):
    manager, combat = world
    base = make_base(turrets=0)
    add(manager, base)
    manager.raids.launch("base_1", base, Vector2(raids.LIVE_RANGE + 5000, 0), combat)
    assert combat.active_bandits == [] and not base.under_attack
    assert any("raided" in text for text, _ in manager.events)


def test_an_undefended_base_loses_goods_and_modules_to_a_raid_it_was_away_for(world):
    manager, combat = world
    base = make_base(turrets=0)
    add(manager, base)
    ore, machinery = base.get_resource_amount("metal_ore"), base.get_resource_amount("machinery")
    manager.raids.launch("base_1", base, Vector2(50000, 0), combat)
    assert base.get_resource_amount("metal_ore") < ore
    assert base.get_resource_amount("machinery") < machinery
    assert base.get_resource_amount("metal_ore") >= ore * (1 - raids.MAX_THEFT) - 1
    assert any(m.hull < m.stats.max_hull for m in base.unique_modules())      # and something took a beating


def test_enough_turrets_turn_a_raid_away_and_nothing_is_lost(world):
    manager, combat = world
    base = make_base(turrets=2)
    add(manager, base)
    threat = raids.threat_of(raids.raid_roster(raids.raid_level(base)))
    assert base.defense_rating() >= threat
    before = dict(base.stored_resources)
    manager.raids.launch("base_1", base, Vector2(50000, 0), combat)
    assert base.stored_resources == before and base.wrecked_count() == 0
    assert any("repelled" in text for text, _ in manager.events)


def test_more_turrets_mean_a_smaller_loss(world):
    manager, combat = world
    losses = []
    for turrets in (0, 2, 4):
        base = make_base(turrets=turrets, extra_modules=5)
        manager.raids.rng = random.Random(3)
        add(manager, base)
        before = sum(base.stored_resources.values())
        manager.raids.launch("base_1", base, Vector2(50000, 0), combat)
        losses.append((before - sum(base.stored_resources.values())) + 100 * base.wrecked_count())
    assert losses == sorted(losses, reverse=True) and losses[0] > losses[-1]


def test_a_live_raid_the_turrets_win_costs_nothing_and_is_announced(world):
    manager, combat = world
    base = make_base(turrets=3)
    add(manager, base)
    before = dict(base.stored_resources)
    manager.raids.launch("base_1", base, Vector2(0, 0), combat)
    for bandit in combat.active_bandits:
        bandit.take_damage(10 ** 6)                          # the defenders cut them down
    manager.events.clear()
    manager.raids.update(1.0, manager.bases, Vector2(0, 0), combat)
    assert not base.under_attack and "base_1" not in manager.raids.live
    assert base.stored_resources == before
    assert any("drove off" in text for text, _ in manager.events)


def test_a_live_raid_that_knocks_modules_out_steals_goods(world):
    manager, combat = world
    base = make_base(turrets=0)
    add(manager, base)
    ore = base.get_resource_amount("metal_ore")
    manager.raids.launch("base_1", base, Vector2(0, 0), combat)
    base.modules[(4, 0)].take_damage(10 ** 6)                # a module is shot to pieces
    for bandit in combat.active_bandits:
        bandit.take_damage(10 ** 6)
    manager.raids.update(1.0, manager.bases, Vector2(0, 0), combat)
    assert base.get_resource_amount("metal_ore") < ore
    assert any("raided" in text for text, _ in manager.events)


def test_raiders_that_outlast_the_siege_withdraw(world):
    manager, combat = world
    base = make_base(turrets=0)
    add(manager, base)
    manager.raids.launch("base_1", base, Vector2(0, 0), combat)
    run(manager, combat, raids.WITHDRAW_AFTER + 5)
    assert combat.active_bandits == [] and not base.under_attack


def test_a_live_raid_the_player_flies_away_from_is_settled_on_numbers(world):
    manager, combat = world
    base = make_base(turrets=0)
    add(manager, base)
    manager.raids.launch("base_1", base, Vector2(0, 0), combat)
    manager.events.clear()
    manager.raids.update(1.0, manager.bases, Vector2(raids.ABANDON_RANGE + 1000, 0), combat)
    assert combat.active_bandits == [] and not base.under_attack
    assert any("raided" in text or "repelled" in text for text, _ in manager.events)


def test_a_new_raid_is_not_started_on_a_base_already_under_one(world):
    manager, combat = world
    base = make_base()
    add(manager, base)
    manager.raids.launch("base_1", base, Vector2(0, 0), combat)
    count = len(combat.active_bandits)
    base.raid_timer = 0.0
    manager.raids.update(1.0, manager.bases, Vector2(0, 0), combat)
    assert len(combat.active_bandits) == count


def test_events_are_handed_over_once(world):
    manager, combat = world
    base = make_base()
    add(manager, base)
    manager.raids.launch("base_1", base, Vector2(50000, 0), combat)
    assert manager.pop_events() and manager.pop_events() == []


# --- raider behaviour ---------------------------------------------------------------------------------

def test_a_raider_goes_for_the_base_not_the_distant_player():
    base = make_base()
    raider = bandit_at(1500, 0)
    raider.raid_base = base
    player = type("P", (), {"position": Vector2(-9000, 0)})()
    assert raider._select_focus(player) is base.focus
    assert base.focus.position.distance_to(base.position) > 0


def test_a_raider_turns_on_a_player_who_is_right_on_top_of_it():
    base = make_base()
    raider = bandit_at(1500, 0)
    raider.raid_base = base
    player = type("P", (), {"position": Vector2(1500, 100)})()
    assert raider._select_focus(player) is player


def test_a_raider_presses_the_attack_and_never_flees():
    base = make_base()
    raider = bandit_at(1500, 0)
    raider.raid_base = base
    raider.current_hull = 1
    player = type("P", (), {"position": Vector2(-9000, 0)})()
    raider._make_decision(raider._select_focus(player))
    assert raider.state in (BanditState.HUNTING, BanditState.ATTACKING)
    assert raider.state != BanditState.FLEEING


def test_a_hurt_raider_with_the_player_close_still_does_not_flee():
    base = make_base()
    raider = bandit_at(1500, 0)
    raider.raid_base = base
    raider.current_hull = 1
    player = type("P", (), {"position": Vector2(1500, 100)})()
    raider._make_decision(raider._select_focus(player))
    assert raider.state != BanditState.FLEEING


def test_an_ordinary_bandit_still_flees_when_hurt():
    bandit = bandit_at(100, 0)
    bandit.current_hull = 1
    player = type("P", (), {"position": Vector2(0, 0)})()
    bandit._make_decision(bandit._select_focus(player))
    assert bandit.state == BanditState.FLEEING


# --- saving ------------------------------------------------------------------------------------------------

def test_hull_and_the_raid_countdown_survive_a_save():
    manager = BaseManager()
    base = make_base(turrets=1)
    add(manager, base)
    base.raid_timer = 321.0
    turret = turret_of(base)
    turret.take_damage(100)
    base.modules[(0, 0)].take_damage(50)
    wrecked = base.modules[(4, 0)]
    wrecked.take_damage(10 ** 6)

    other = BaseManager()
    assert other.load_bases(manager.save_bases())
    loaded = other.get_base("base_1")
    assert loaded.raid_timer == 321.0
    assert turret_of(loaded).hull == turret.hull
    assert loaded.modules[(0, 0)].hull == base.modules[(0, 0)].hull
    assert loaded.modules[(4, 0)].wrecked and loaded.modules[(4, 0)].hull == 0


def test_a_save_from_before_raids_loads_with_full_hull_and_no_countdown():
    manager = BaseManager()
    add(manager, make_base())
    data = manager.save_bases()
    for entry in data["bases"].values():
        entry.pop("raid_timer", None)
        entry.pop("core_hull", None)
        for module in entry["modules"]:
            module.pop("hull", None)
    other = BaseManager()
    assert other.load_bases(data)
    base = other.get_base("base_1")
    assert base.raid_timer is None
    assert all(m.hull == m.stats.max_hull and not m.wrecked for m in base.unique_modules())


def test_a_new_game_forgets_raids():
    manager = BaseManager()
    base = make_base()
    add(manager, base)
    manager.raids.launch("base_1", base, Vector2(0, 0), CombatManager())
    manager.reset()
    assert manager.raids.live == {} and manager.events == []
