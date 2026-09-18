"""Rank ladder derived from player reputation. Reputation itself is tracked
in MissionManager; rank is always computed on demand rather than stored, so
there is nothing new to persist or keep in sync.
"""

RANKS = [
    ("Rookie", 0),
    ("Trader", 15),
    ("Merchant", 40),
    ("Captain", 80),
    ("Legend", 150),
]

TIER_4_MIN_REPUTATION = 80  # Captain - gates the top tier of ship upgrades


def get_rank_name(reputation: int) -> str:
    """Get the rank name for a given reputation value."""
    name = RANKS[0][0]
    for rank_name, threshold in RANKS:
        if reputation >= threshold:
            name = rank_name
        else:
            break
    return name


def get_next_rank(reputation: int):
    """Get (name, reputation_needed) for the next rank, or None if maxed out."""
    for rank_name, threshold in RANKS:
        if reputation < threshold:
            return rank_name, threshold
    return None
