"""Text shown in the Logbook: chapter summaries, decoded ledger entries, and
short faction descriptions. Plain ASCII (the default pygame font cannot draw
anything else).
"""

CHAPTERS = {
    "prologue": (
        "Prologue: A Dead Man's Ship",
        "You fly a ship that belonged to a trader named Jessup Vane, who "
        "vanished three weeks ago. A retired dock master named Hale thinks "
        "Vane's disappearance was no accident, and that his ledger is the "
        "reason. Earn a trader's license and return to him.",
    ),
    "act_1": ("Act 1: The Ledger", "The ledger points into every faction's territory."),
    "act_2": ("Act 2: The Guild's Secret", "Someone is funding the pirates."),
    "act_3": ("Act 3: Border War", "The truth shifts the borders."),
    "act_4": ("Act 4: The Signal", "The last entry points past the edge of known space."),
}

LEDGER_ENTRIES = {
    "ledger_cover": (
        "The Ledger",
        "A battered ledger in Jessup Vane's private shorthand: sector "
        "coordinates, cargo tallies, and one word at the end of each line - "
        "Guild, Independent, or Pirate. Hale cannot make sense of it. "
        "Neither can you, yet.",
    ),
}

FACTION_BLURBS = {
    "Trade Guild": "Runs the safest, busiest sectors. Prices are fair and patrols are common, "
                   "but the Guild keeps careful records of everything that passes through.",
    "Independent": "Free stations outside any bloc. Quiet, modest, and always the first to "
                   "be squeezed when the big factions quarrel.",
    "Pirate Territory": "Lawless space. Raiders are frequent, honest traders are rare, "
                        "and the pay for risky work is high.",
}
