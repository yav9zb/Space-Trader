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
        Choice("Fair enough.", next=None),
    ],
))

_add(Node(
    "hale_return", HALE,
    "Back again, captain. Anything to report?",
    choices=[
        Choice("I have earned my trader's license.", next="hale_ready",
               requires={"min_rank": "Trader", "not_flag": "hale_ready_ack"}),
        Choice("Remind me about the ledger.", next="hale_ledger"),
        Choice("Where did you find it?", next="hale_friend"),
        Choice("Just passing through.", next=None),
    ],
))

_add(Node(
    "hale_ready", HALE,
    "So you have. A trader's license means somebody trusts you with cargo. "
    "That is a start.\n\n"
    "I need time with the first entry before I send you anywhere near it. "
    "Keep trading, keep your head down, and check in with me again soon.",
    on_enter=[{"type": "set_flag", "name": "hale_ready_ack"}],
    choices=[
        Choice("I will keep my head down.", next=None),
    ],
))
