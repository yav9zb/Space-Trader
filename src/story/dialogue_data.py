"""Authored dialogue, keyed by node id. Content is added per campaign phase;
tests/test_story_data.py validates the whole graph (see story/dialogue.py).
All text must be plain ASCII.
"""

from typing import Dict

from .dialogue import Choice, Node

HALE = "Dock Master Hale"

NODES: Dict[str, Node] = {}


def _add(node: Node):
    NODES[node.id] = node


# --- Dock Master Hale (prologue) ---------------------------------------------

_add(Node(
    "hale_intro", HALE,
    "Easy there, captain. You are flying a dead man's ship, and I would know "
    "that hull anywhere. It belonged to Jessup Vane. Best trader this side of "
    "the sector line, and the only man who ever paid his dock fees early.\n\n"
    "He has been gone three weeks. The Guild says his ship drifted back on its "
    "own. I say ships do not do that.",
    on_enter=[{"type": "set_flag", "name": "met_hale"}],
    choices=[
        Choice("Jessup Vane was your friend?", next="hale_friend"),
        Choice("I bought this ship at auction.", next="hale_auction"),
        Choice("I do not have time for this.", next=None),
    ],
))

_add(Node(
    "hale_auction", HALE,
    "Auction? The Guild does not auction a ship it has not finished with. "
    "Whoever sold you this vessel wanted it out of their hands quickly.\n\n"
    "Tell me, did the paperwork name the previous owner?",
    choices=[
        Choice("No. It was blank.", next="hale_friend"),
        Choice("I never looked.", next="hale_friend"),
    ],
))

_add(Node(
    "hale_friend", HALE,
    "Thirty years, and he never once told me what he carried. But the week "
    "before he vanished he left a ledger in my safe with a note: if anything "
    "happens, it goes to whoever flies my ship.\n\n"
    "I did not expect that to be a stranger. Keep it. Read it. I cannot make "
    "sense of it - his own shorthand, all coordinates and tally marks.",
    on_enter=[{"type": "add_ledger_entry", "id": "ledger_cover"}],
    choices=[
        Choice("What is in the ledger?", next="hale_ledger"),
        Choice("Why would he trust a stranger?", next="hale_why"),
    ],
))

_add(Node(
    "hale_ledger", HALE,
    "Pages of numbers. Sector coordinates, cargo counts, and a word at the end "
    "of each line: Guild, Independent, Pirate. He was tracking something "
    "across all three. I did not like that when I saw it, and I like it less "
    "now.\n\n"
    "You are not ready to chase it, though. Make some honest runs first. Build "
    "a name. When you have earned a trader's license, come and find me.",
    on_enter=[
        {"type": "add_ledger_entry", "id": "ledger_cover"},
        {"type": "set_flag", "name": "hale_told_ledger"},
    ],
    choices=[
        Choice("I will earn that license.", next=None,
               requires={"not_story_started": "prologue_1"},
               effects=[{"type": "start_story_mission", "mission_id": "prologue_1"}]),
        Choice("I will be back.", next=None),
    ],
))

_add(Node(
    "hale_why", HALE,
    "Because he trusted his ship to find its way to someone worth trusting. I "
    "will not pretend I am sure you are that person. Prove it. Complete some "
    "contracts and come back with a trader's license.",
    on_enter=[{"type": "set_flag", "name": "hale_told_ledger"}],
    choices=[
        Choice("I will earn that license.", next=None,
               requires={"not_story_started": "prologue_1"},
               effects=[{"type": "start_story_mission", "mission_id": "prologue_1"}]),
        Choice("Fair enough.", next=None),
    ],
))

_add(Node(
    "hale_return", HALE,
    "Back again, captain. Anything to report?",
    choices=[
        Choice("I have earned my trader's license.", next="hale_ready",
               requires={"story_active": "prologue_1", "min_rank": "Trader"}),
        Choice("I found Vane's locker.", next="hale_locker",
               requires={"flag": "prologue_entry_found", "not_story_started": "prologue_3"}),
        Choice("I met the courier.", next="hale_epilogue",
               requires={"flag": "prologue_complete", "not_flag": "prologue_epilogue_seen"}),
        Choice("About that ledger...", next="hale_ledger"),
        Choice("Where did you find it?", next="hale_friend"),
        Choice("Just passing through.", next=None),
    ],
))

_add(Node(
    "hale_ready", HALE,
    "So you have. A trader's license means somebody trusts you with cargo. "
    "That is a start.\n\n"
    "I have been through the first entry line by line. It points to a berth at "
    "{station:prologue_2.a}. If Jessup left anything behind, it will be there. "
    "Go and look, then come back and tell me what you find.",
    on_enter=[
        {"type": "bump_counter", "name": "story:hale_license_shown"},
        {"type": "start_story_mission", "mission_id": "prologue_2"},
    ],
    choices=[
        Choice("I will look into it.", next=None),
    ],
))

_add(Node(
    "hale_locker", HALE,
    "A locker, a page, and a name: Reyes. I have heard that name. A courier, "
    "Independent, runs sealed parcels between the quiet stations. If Jessup "
    "trusted anyone, it was her.\n\n"
    "She is waiting at {station:prologue_3.b}. Go and see her. And captain - "
    "be careful what you say about the Guild out there.",
    on_enter=[{"type": "start_story_mission", "mission_id": "prologue_3"}],
    choices=[
        Choice("I will be careful.", next=None),
    ],
))

_add(Node(
    "hale_epilogue", HALE,
    "Reyes told you that? Then Jessup was right to be afraid, and so are we. "
    "I have been a dock master for forty years and I have never wanted so "
    "badly to be wrong.\n\n"
    "The ledger's next lines point three ways, and I know someone at the end "
    "of each. Captain Rourke flew with Jessup, at {station:rourke}. An "
    "auditor named Voss, who keeps her head down inside the Guild, at "
    "{station:voss}. And Kestrel, who sells what pirates know, at "
    "{station:kestrel}. Hear what each has to say, then come back to me.",
    on_enter=[
        {"type": "set_flag", "name": "prologue_epilogue_seen"},
        {"type": "set_chapter", "chapter": "act_1"},
    ],
    choices=[
        Choice("I will hear them out.", next=None),
    ],
))

# --- Scenes shown automatically when a story mission completes ---------------

_add(Node(
    "cache_found", "Dockhand Pell",
    "You are the one asking about Vane's berth? He paid for it a year in "
    "advance and never used it twice. There is a locker. He told me the key "
    "was the ship itself, so I suppose you have it.\n\n"
    "Inside: a folded page in the same shorthand as the ledger, and one line "
    "in plain writing. 'If you are reading this, go to Reyes. Do not trust the "
    "Guild with this.' I did not read the rest. I never read what is not mine.",
    choices=[
        Choice("Thank you.", next=None),
    ],
))

_add(Node(
    "courier_meeting", "Courier Reyes",
    "You took your time. Vane said someone would come, though he thought it "
    "would be sooner.\n\n"
    "He is dead, you know. Not drifted, not lost. The Guild called it an "
    "accident because that is the tidiest word. He kept his accounts in that "
    "shorthand because he was tracing where Guild money really goes, and it "
    "does not go where the Guild says it does.\n\n"
    "I will not say more here. Take this copy of his last entry and keep it "
    "close. When you know what you want to do about it, find Hale. He will "
    "know who else to trust.",
    choices=[
        Choice("I will find out who did this.", next=None),
    ],
))


# The campaign proper (Acts 1 to 4) is authored in dialogue_acts.py and
# registers its nodes through add_node above.
add_node = _add

from . import dialogue_acts  # noqa: E402,F401
