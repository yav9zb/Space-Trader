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
    "act_1": (
        "Act 1: The Ledger",
        "Vane's ledger points into every faction's territory. Three people can "
        "each explain a piece of it: Captain Rourke, who flew with him, Auditor "
        "Voss of the Trade Guild, and Kestrel, a broker in Pirate Territory. "
        "Hear all three, then return to Hale.",
    ),
    "act_2": (
        "Act 2: The Guild's Secret",
        "Someone is paying the pirates. Gather proof from the Guild's own "
        "records, the pirate who carries the money, and a clerk willing to "
        "testify, then take it to Hale.",
    ),
    "act_3": (
        "Act 3: Border War",
        "You hold evidence that could break the Guild. What you do with it "
        "will redraw the borders, and not everyone will accept the new ones.",
    ),
    "act_4": (
        "Act 4: The Signal",
        "Vane's last entry, decoded, points past the edge of charted space. "
        "Whatever is out there, someone has spent a great deal to keep every "
        "trader from finding it.",
    ),
}

# Shown in place of the prologue summary once its missions are done
PROLOGUE_DONE_SUMMARY = (
    "Courier Reyes confirmed it: Jessup Vane was killed, and the Guild buried "
    "it as an accident. He was tracing where Guild money really goes. Hale "
    "has nothing more for you until the ledger gives up its next secret."
)

LEDGER_ENTRIES = {
    "ledger_cover": (
        "The Ledger",
        "A battered ledger in Jessup Vane's private shorthand: sector "
        "coordinates, cargo tallies, and one word at the end of each line - "
        "Guild, Independent, or Pirate. Hale cannot make sense of it. "
        "Neither can you, yet.",
    ),
    "ledger_entry_1": (
        "Entry One: The Berth",
        "Vane's first coded line led to a rented berth and a locker. Inside: a "
        "page in his shorthand and a note naming a courier, Reyes. 'Do not "
        "trust the Guild with this.'",
    ),
    "ledger_entry_2": (
        "Entry Two: Reyes",
        "The courier Reyes confirms Vane was killed and that the Guild called it "
        "an accident. He was tracing where Guild money really goes. She gave "
        "you a copy of his last entry.",
    ),
}

LEDGER_ENTRIES.update({
    "ledger_entry_3": (
        "Entry Three: The Raids",
        "Rourke matched Vane's run dates against the raids that hit them. Every "
        "ambush came within an hour of a Guild manifest being filed. The "
        "pirates were not stumbling onto his cargo. They were told.",
    ),
    "ledger_entry_4": (
        "Entry Four: The Manifests",
        "The manifests Voss wanted show a recurring Guild payment under a code "
        "name: the Hollow Account. It is paid monthly, and it is never "
        "accounted for in any Guild report.",
    ),
    "ledger_entry_5": (
        "Entry Five: The Broker",
        "Kestrel confirmed the other half: pirate captains are paid on the "
        "first of the month, in clean credits, by someone who never shows "
        "their face. Raids rise and fall with the payments.",
    ),
    "ledger_entry_6": (
        "Entry Six: The Hollow Ledgers",
        "The Archivist's copies are damning. Ten pirate captains, one "
        "account, and a pattern: the Guild pays them to keep insurance "
        "premiums and escort fees high on every lane it does not control.",
    ),
    "ledger_entry_7": (
        "Entry Seven: The Receipts",
        "Paymaster Dross carried the receipts, and each is signed with the "
        "same mark. The Hollow Account answers to one person: Director "
        "Marrow of the Trade Guild.",
    ),
    "ledger_entry_8": (
        "Entry Eight: The Witness",
        "A Guild clerk who signed the payments reached safety and gave a "
        "full statement. It matches the ledgers, the receipts and Vane's "
        "pages line for line.",
    ),
    "ledger_entry_9": (
        "Entry Nine: Marrow's Offer",
        "Marrow does not deny the Hollow Account. He wants a captain who "
        "understands that a safe galaxy is a poor one, and who will not "
        "mind who pays for that. He offered you a place at his table.",
    ),
    "ledger_entry_10": (
        "Entry Ten: The Last Page",
        "Dr. Okoye decoded Vane's last entry. It is a position, far past the "
        "edge of charted space, and a note: 'Every captain on the Hollow "
        "Account sits on a lane that leads here. The money buys silence "
        "about it. It is listening.'",
    ),
    "ledger_entry_11": (
        "Entry Eleven: The Signal",
        "A repeating transmission from the heart of the sector, older than "
        "any faction. The Guild has been buying silence about it for years, "
        "and a fleet is waiting around it.",
    ),
})

# What the Story page says between a chapter's last mission and the next
ACT_DONE_SUMMARIES = {
    "act_1": (
        "Rourke, Voss and Kestrel have each given you a piece. Hale will want "
        "to hear it."
    ),
    "act_2": (
        "You have the Guild's ledgers, the paymaster's receipts and a witness. "
        "Hale will help you decide what to do with them."
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
