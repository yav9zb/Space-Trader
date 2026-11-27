"""Undocking: the ship that has just left a station is not pulled straight back in by
auto-docking; it can dock again once it has flown clear, or when the player asks."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pygame import Vector2

from src.docking.docking_manager import CLEAR_OF_STATION, DockingManager
from src.docking.docking_state import DockingResult, DockingState
from src.entities.ship import Ship
from src.entities.station import Station, StationType

DT = 1 / 30


def docked():
    station = Station(1000, 1000, StationType.TRADING)
    ship = Ship(0, 0)
    ship.position = Vector2(1000 - (station.size + ship.size + 5), 1000)
    ship.velocity = Vector2(0, 0)
    manager = DockingManager()
    for _ in range(300):
        manager.update(ship, [station], DT)
    assert manager.docking_state == DockingState.DOCKED
    return manager, ship, station


def run(manager, ship, station, seconds):
    for _ in range(int(seconds / DT)):
        manager.update(ship, [station], DT)


def undock(manager, ship, station):
    assert manager.attempt_undocking(ship) == DockingResult.SUCCESS
    run(manager, ship, station, manager.docking_duration + 0.5)


def test_the_ship_stays_undocked_after_leaving_the_station():
    manager, ship, station = docked()
    undock(manager, ship, station)
    run(manager, ship, station, 10)
    assert manager.docking_state != DockingState.DOCKED and not manager.is_docking_in_progress()
    assert manager.undocked_from is station


def test_the_ship_is_not_pulled_back_in_with_the_default_and_the_relaxed_settings():
    for speed in (30.0, 50.0, 80.0):
        manager, ship, station = docked()
        manager.max_docking_speed = speed
        undock(manager, ship, station)
        run(manager, ship, station, 10)
        assert manager.docking_state != DockingState.DOCKED


def test_it_says_why_while_the_ship_is_still_beside_the_station():
    manager, ship, station = docked()
    undock(manager, ship, station)
    run(manager, ship, station, 1)
    assert "Fly clear" in manager.get_status_message()


def test_flying_clear_and_coming_back_docks_again():
    manager, ship, station = docked()
    undock(manager, ship, station)
    ship.position = station.position + Vector2(station.size + ship.size + 20 + CLEAR_OF_STATION + 50, 0)
    run(manager, ship, station, 0.5)
    assert manager.undocked_from is None
    ship.position = station.position + Vector2(station.size + ship.size + 5, 0)
    ship.velocity = Vector2(0, 0)
    run(manager, ship, station, 5)
    assert manager.docking_state == DockingState.DOCKED


def test_the_dock_key_still_docks_right_after_undocking():
    manager, ship, station = docked()
    undock(manager, ship, station)
    assert manager.attempt_manual_docking(ship, [station]) == DockingResult.SUCCESS
    run(manager, ship, station, 3)
    assert manager.docking_state == DockingState.DOCKED


def test_a_different_station_still_auto_docks():
    manager, ship, station = docked()
    undock(manager, ship, station)
    other = Station(5000, 5000, StationType.MINING)
    ship.position = Vector2(5000 - (other.size + ship.size + 5), 5000)
    ship.velocity = Vector2(0, 0)
    for _ in range(300):
        manager.update(ship, [station, other], DT)
    assert manager.docking_state == DockingState.DOCKED and manager.target_station is other
