"""The player's outpost: a freed station Hale lets the player claim at the
end of Act 3. Its one benefit is passive income: it accrues credits while
the game is played and pays them out when the player docks there. Everything
is stored as story state (the station name and the play time of the last
payout), so it saves and loads with the campaign.
"""

RATE_PER_MINUTE = 25
CAP = 4000

STATION_KEY = "outpost"            # the story_state.npc_stations key
COLLECTED_AT = "outpost_collected_at"


def is_claimed(story) -> bool:
    return story.has_flag("outpost_claimed") and bool(story.npc_stations.get(STATION_KEY))


def claim(game_engine, station_name: str) -> bool:
    """Make a station the player's outpost. Its income starts from now."""
    story = game_engine.story_state
    if not station_name or is_claimed(story):
        return False
    story.npc_stations[STATION_KEY] = station_name
    story.set_flag("outpost_claimed")
    story.set_flag(COLLECTED_AT, float(getattr(game_engine, "play_time", 0.0)))
    story.record_event("outpost_claimed", station=station_name)

    from ..ui.notifications import notifications
    notifications.push(f"Outpost claimed: {station_name}", duration=7.0, color=(150, 230, 170))
    return True


def pending_income(story, play_time: float) -> int:
    """Credits waiting at the outpost."""
    if not is_claimed(story):
        return 0
    since = float(story.get_flag(COLLECTED_AT, play_time))
    minutes = max(0.0, play_time - since) / 60.0      # a load can rewind play time
    return min(CAP, int(minutes * RATE_PER_MINUTE))


def collect(game_engine, station) -> int:
    """Pay out what has accrued if this station is the outpost. Returns the
    credits paid."""
    story = game_engine.story_state
    if not is_claimed(story) or station.name != story.npc_stations[STATION_KEY]:
        return 0
    play_time = float(getattr(game_engine, "play_time", 0.0))
    amount = pending_income(story, play_time)
    story.set_flag(COLLECTED_AT, play_time)
    if amount > 0:
        game_engine.ship.credits += amount
        from ..ui.notifications import notifications
        notifications.push(f"Outpost income collected: {amount:,} credits", duration=6.0,
                           color=(150, 230, 170))
    return amount
