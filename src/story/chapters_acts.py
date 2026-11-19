"""The campaign proper: Acts 1 to 4, as story mission data. The prologue is in
chapters.py. Station names are never authored; waypoints describe where to
look (faction, distance from spawn, optionally a station type).
"""

from .chapters import STORY_MISSIONS, Stage, StoryMissionDef, Waypoint

GUILD = "Trade Guild"
INDEPENDENT = "Independent"
PIRATE = "Pirate Territory"

# Where the Signal is, in sectors as the Navigation HUD shows them. Far enough
# out that the trip is a journey, whatever the world seed.
SIGNAL_SECTOR = (26, -22)


def _add(definition: StoryMissionDef):
    STORY_MISSIONS[definition.id] = definition


# --- Act 1: The Ledger --------------------------------------------------------

_add(StoryMissionDef(
    id="act1_1",
    title="Vane's Last Run",
    description=(
        "Captain Rourke has a freighter of salvage that must reach {b}. Every "
        "run on that lane has been hit for a month, just as Vane's was. Keep "
        "the freighter alive."
    ),
    giver="rourke",
    waypoints={"b": Waypoint(faction=INDEPENDENT, min_ring=3, max_ring=5)},
    stages=(
        Stage("escort", "Escort Rourke's freighter to {b}",
              {"from": "giver", "to": "b", "ambush": "fighter_squad"}),
    ),
    reward_credits=700,
    reputation_bonus=8,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_3"},
        {"type": "adjust_standing", "faction": INDEPENDENT, "amount": 3},
        {"type": "show_dialogue", "node": "rourke_thanks"},
    ),
))

_add(StoryMissionDef(
    id="act1_2",
    title="The Auditor's Request",
    description=(
        "Auditor Voss wants copies of the manifests filed at {a} the week Vane "
        "died. She cannot be seen collecting them herself."
    ),
    giver="voss",
    waypoints={"a": Waypoint(faction=GUILD, min_ring=3, max_ring=6)},
    stages=(
        Stage("dock_at", "Dock at {a} and collect the manifests", {"waypoint": "a"}),
        Stage("counter", "Bring the manifests back to Auditor Voss",
              {"counter": "story:voss_manifests"}),
    ),
    reward_credits=800,
    reputation_bonus=8,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_4"},
        {"type": "adjust_standing", "faction": GUILD, "amount": 3},
    ),
))

_add(StoryMissionDef(
    id="act1_3",
    title="A Broker's Favor",
    description=(
        "Kestrel sells what she knows, and she is not interested in credits. "
        "She wants the raiders working the lanes around her station thinned "
        "out. Do that and she will talk."
    ),
    giver="kestrel",
    stages=(
        Stage("destroy_bandits", "Destroy 6 bandits", {"count": 6}),
        Stage("counter", "Tell Kestrel it is done", {"counter": "story:kestrel_favor"}),
    ),
    reward_credits=900,
    reputation_bonus=8,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_5"},
        {"type": "adjust_standing", "faction": PIRATE, "amount": 3},
    ),
))

# --- Act 2: The Guild's Secret -----------------------------------------------

_add(StoryMissionDef(
    id="act2_1",
    title="Paper Trail",
    description=(
        "The Archivist can read the Guild's sealed ledgers but cannot carry "
        "them out. He needs someone to collect his copies at {a} and bring "
        "them to him."
    ),
    giver="archivist",
    waypoints={"a": Waypoint(faction=GUILD, station_types=("Military Base",),
                             min_ring=5, max_ring=9)},
    stages=(
        Stage("dock_at", "Dock at {a} and collect the copied ledgers", {"waypoint": "a"}),
        Stage("counter", "Bring the copies to the Archivist",
              {"counter": "story:archivist_papers"}),
    ),
    reward_credits=1200,
    reputation_bonus=10,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_6"},
    ),
))

_add(StoryMissionDef(
    id="act2_2",
    title="The Paymaster",
    description=(
        "The Hollow Account pays ten pirate captains. One of them, Dross, "
        "carries the receipts himself and is holed up near {a}. Kestrel wants "
        "him gone, and you want what he is carrying."
    ),
    giver="kestrel",
    waypoints={"a": Waypoint(faction=PIRATE, min_ring=5, max_ring=9)},
    stages=(
        Stage("fleet", "Destroy Paymaster Dross and his escort near {a}",
              {"at": "a", "ships": ["boss", "heavy", "fighter", "fighter"],
               "boss_name": "Paymaster Dross"}),
        Stage("counter", "Bring the receipts to Kestrel", {"counter": "story:paymaster_receipts"}),
    ),
    reward_credits=2200,
    reputation_bonus=12,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_7"},
        {"type": "adjust_standing", "faction": PIRATE, "amount": 2},
    ),
))

_add(StoryMissionDef(
    id="act2_3",
    title="The Witness",
    description=(
        "A Guild clerk who signed the Hollow payments will testify, but only "
        "if he reaches {b} alive. Rourke has put him aboard a freighter. The "
        "Guild knows."
    ),
    giver="rourke",
    waypoints={"b": Waypoint(faction=INDEPENDENT, min_ring=4, max_ring=7)},
    stages=(
        Stage("escort", "Escort the witness to {b}",
              {"from": "giver", "to": "b", "ambush": "heavy_escort"}),
    ),
    reward_credits=1800,
    reputation_bonus=10,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_8"},
        {"type": "adjust_standing", "faction": INDEPENDENT, "amount": 3},
        {"type": "show_dialogue", "node": "witness_delivered"},
    ),
))

_add(StoryMissionDef(
    id="act2_4",
    title="Marrow's Offer",
    description=(
        "Voss has arranged a private meeting at {a} with someone close to "
        "Director Marrow, who runs the Hollow Account. They want to talk "
        "about what you have found."
    ),
    giver="voss",
    waypoints={"a": Waypoint(faction=GUILD, min_ring=6, max_ring=9)},
    stages=(
        Stage("dock_at", "Dock at {a} for the meeting", {"waypoint": "a"}),
        Stage("counter", "Tell Voss what was offered", {"counter": "story:voss_offer"}),
    ),
    reward_credits=1500,
    reputation_bonus=10,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_9"},
    ),
))

# --- Act 3: Border War --------------------------------------------------------

_add(StoryMissionDef(
    id="act3_1",
    title="Three Roads",
    description=(
        "You hold the proof that the Guild pays the pirates it claims to "
        "fight. What you do with it decides who controls the lanes."
    ),
    giver="hale",
    stages=(
        Stage("counter", "Decide what to do with the evidence",
              {"counter": "story:choice_made"}),
    ),
    reward_credits=500,
    reputation_bonus=5,
))

_add(StoryMissionDef(
    id="act3_2",
    title="The New Frontier",
    description=(
        "With the old borders broken, warbands are carving up the new "
        "frontier. One has taken {a}. Break it before it becomes permanent."
    ),
    giver="hale",
    waypoints={"a": Waypoint(faction=INDEPENDENT, min_ring=4, max_ring=8)},
    stages=(
        Stage("fleet", "Destroy the warband near {a}",
              {"at": "a", "ships": ["boss", "heavy", "heavy", "fighter", "fighter"],
               "boss_name": "Warband Chief"}),
    ),
    reward_credits=3500,
    reputation_bonus=15,
))

_add(StoryMissionDef(
    id="act3_3",
    title="The Observatory",
    description=(
        "Dr. Okoye can decode Vane's last page, but her instruments need "
        "calibrating against the array at {a}. Dock there, then come back."
    ),
    giver="okoye",
    waypoints={"a": Waypoint(faction=INDEPENDENT, station_types=("Research Station",),
                             min_ring=7, max_ring=10)},
    stages=(
        Stage("dock_at", "Dock at {a} and calibrate the array", {"waypoint": "a"}),
        Stage("counter", "Return to Dr. Okoye", {"counter": "story:okoye_calibrated"}),
    ),
    reward_credits=2500,
    reputation_bonus=12,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_10"},
        {"type": "set_chapter", "chapter": "act_4"},
    ),
))

# --- Act 4: The Signal --------------------------------------------------------

_add(StoryMissionDef(
    id="act4_1",
    title="Fit for the Dark",
    description=(
        "The Signal comes from beyond anything charted. Dr. Okoye will not "
        "send an unproven pilot out there. Earn the rank of Captain, then "
        "come to her."
    ),
    giver="okoye",
    stages=(
        Stage("earn_rank", "Earn the rank of Captain", {"rank": "Captain"}),
        Stage("counter", "Tell Dr. Okoye you are ready", {"counter": "story:okoye_ready"}),
    ),
    reward_credits=3000,
    reputation_bonus=10,
))

_add(StoryMissionDef(
    id="act4_2",
    title="Past the Last Light",
    description=(
        "The decoded entry gives a position: Sector (%d, %d), well past the "
        "last charted station. Fly there." % SIGNAL_SECTOR
    ),
    giver="okoye",
    stages=(
        Stage("reach_sector", "Reach Sector (%d, %d)" % SIGNAL_SECTOR,
              {"x": SIGNAL_SECTOR[0], "y": SIGNAL_SECTOR[1], "radius": 1}),
    ),
    reward_credits=4000,
    reputation_bonus=15,
    on_complete=(
        {"type": "add_ledger_entry", "id": "ledger_entry_11"},
        {"type": "start_story_mission", "mission_id": "act4_3"},
        {"type": "show_dialogue", "node": "signal_arrival"},
    ),
))

_add(StoryMissionDef(
    id="act4_3",
    title="The Source",
    description=(
        "Something is broadcasting from the heart of this sector, and a "
        "fleet is guarding it. Whoever has been paying for the lanes to stay "
        "dangerous wanted nobody to get this far."
    ),
    giver="okoye",
    stages=(
        Stage("fleet", "Destroy the fleet guarding the Signal",
              {"sector": SIGNAL_SECTOR,
               "ships": ["boss", "boss", "heavy", "heavy", "fighter", "fighter"],
               "boss_name": "The Warden"}),
    ),
    reward_credits=8000,
    reputation_bonus=25,
    on_complete=(
        {"type": "set_flag", "name": "signal_fleet_broken"},
        {"type": "show_dialogue", "node": "signal_choice"},
    ),
))
