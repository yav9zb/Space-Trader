"""Acts 1 to 4: contact dialogue, mission hand-offs and scenes. Plain ASCII
only. Conventions used throughout:

- An offer node explains a job; picking "I will do it" leads to an accept node
  whose on_enter starts the mission, so its text can name the waypoint
  station ({station:<mission>.<waypoint>}) once it has been placed.
- A report node bumps the counter the mission's last stage is waiting on.
- Hub nodes (the *_return nodes) show only the choices that apply right now.
"""

from .chapters_acts import SIGNAL_SECTOR
from .dialogue import Choice, Node
from .dialogue_data import HALE, NODES, add_node as _add
from .outpost import CAP, RATE_PER_MINUTE

ROURKE = "Captain Rourke"
VOSS = "Auditor Voss"
KESTREL = "Kestrel"
ARCHIVIST = "The Archivist"
OKOYE = "Dr. Okoye"

# --- Hale: Act 1 and 2 debriefs, the choice, the frontier ---------------------

_hale_hub = NODES["hale_return"]
_hale_extra = [
    Choice("Where can I find them again?", next="hale_contacts",
           requires={"flag": "prologue_epilogue_seen", "not_flag": "act1_debriefed"}),
    Choice("Rourke, Voss and Kestrel have each told me their part.", next="hale_act1_end",
           requires={"story_done_all": ["act1_1", "act1_2", "act1_3"],
                     "not_flag": "act1_debriefed"}),
    Choice("I have the ledgers, the receipts and a witness.", next="hale_act2_end",
           requires={"story_done_all": ["act2_1", "act2_2", "act2_3", "act2_4"],
                     "not_flag": "act2_debriefed"}),
    Choice("What do I do with all of this?", next="hale_choice",
           requires={"flag": "act2_debriefed", "not_story_started": "act3_1"}),
    Choice("About the choice I have to make...", next="hale_choice",
           requires={"story_active": "act3_1"}),
    Choice("About the station we freed.", next="hale_outpost",
           requires={"story_done": "act3_2", "not_flag": "outpost_claimed"}),
    Choice("How is my outpost doing?", next="hale_outpost_status",
           requires={"flag": "outpost_claimed"}),
    Choice("The frontier is in chaos.", next="hale_frontier",
           requires={"story_done": "act3_1", "not_story_started": "act3_2"}),
]
_hale_hub.choices[3:3] = _hale_extra     # after the prologue choices, before the chat

_add(Node(
    "hale_contacts", HALE,
    "Captain Rourke is at {station:rourke}. Auditor Voss is at {station:voss}, "
    "in Guild space, so mind your manners. And Kestrel keeps to "
    "{station:kestrel}, in Pirate Territory. Dock, then press the Talk key to "
    "speak to whoever is waiting.",
    choices=[Choice("Thank you.", next=None)],
))

_add(Node(
    "hale_act1_end", HALE,
    "Three people, three pieces. Rourke says the raids on Jessup's runs were "
    "timed to Guild filings. Voss found a payment with no owner. Kestrel says "
    "the raiders are paid on the first of every month.\n\n"
    "Put together, someone inside the Guild is paying pirates to prey on "
    "honest traders. I have been a dock master for forty years and I have "
    "never wanted so badly to be wrong.\n\n"
    "There is a clerk who reads every record the Guild keeps. They call him "
    "the Archivist. Find him at {station:archivist}.",
    on_enter=[
        {"type": "set_flag", "name": "act1_debriefed"},
        {"type": "set_chapter", "chapter": "act_2"},
    ],
    choices=[Choice("I will find him.", next=None)],
))

_add(Node(
    "hale_act2_end", HALE,
    "Ledgers, receipts and a witness who will say it out loud. And the name "
    "on every page: Marrow. I knew Director Marrow when he was a junior "
    "factor counting crates. He was always sure the galaxy would be better "
    "run if he ran it.\n\n"
    "You are standing where Jessup stood, captain, and you know where that "
    "ended. Whatever you decide, decide it knowing that. There is also a "
    "scientist named Okoye at {station:okoye} who has been asking after "
    "Jessup's last page. When the dust settles, see her.",
    on_enter=[
        {"type": "set_flag", "name": "act2_debriefed"},
        {"type": "set_chapter", "chapter": "act_3"},
    ],
    choices=[
        Choice("What should I do with the evidence?", next="hale_choice"),
        Choice("I need time to think.", next=None),
    ],
))

_add(Node(
    "hale_choice", HALE,
    "You have three roads, and I will not pretend any of them is clean.\n\n"
    "Expose it: put the ledgers in front of every station in the sector. The "
    "Guild will be humbled and the pirates will lose their paymaster, but "
    "the Guild will not forgive whoever did it.\n\n"
    "Join Marrow: he offered you a seat. The lanes would be safe, because "
    "the Guild would own all of them, and the price of that safety is whose "
    "name is on the contracts.\n\n"
    "Stay free: broker a quiet end to the payments and keep the independent "
    "stations out of it. Slower, and nobody thanks you.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act3_1"}],
    choices=[
        Choice("Expose the Hollow Account.", next="hale_after_expose",
               effects=[
                   {"type": "set_flag", "name": "path_chosen"},
                   {"type": "set_flag", "name": "path_expose"},
                   {"type": "adjust_standing", "faction": "Trade Guild", "amount": -25},
                   {"type": "adjust_standing", "faction": "Independent", "amount": 15},
                   {"type": "adjust_standing", "faction": "Pirate Territory", "amount": -5},
                   {"type": "flip_region", "from": "Trade Guild", "faction": "Independent"},
                   {"type": "flip_region", "from": "Pirate Territory", "faction": "Independent"},
                   {"type": "bump_counter", "name": "story:choice_made"},
               ]),
        Choice("Accept Marrow's offer.", next="hale_after_join",
               effects=[
                   {"type": "set_flag", "name": "path_chosen"},
                   {"type": "set_flag", "name": "path_join"},
                   {"type": "adjust_standing", "faction": "Trade Guild", "amount": 30},
                   {"type": "adjust_standing", "faction": "Independent", "amount": -15},
                   {"type": "flip_region", "from": "Independent", "faction": "Trade Guild"},
                   {"type": "flip_region", "from": "Pirate Territory", "faction": "Trade Guild"},
                   {"type": "bump_counter", "name": "story:choice_made"},
               ]),
        Choice("Broker a truce and keep the lanes free.", next="hale_after_independent",
               effects=[
                   {"type": "set_flag", "name": "path_chosen"},
                   {"type": "set_flag", "name": "path_independent"},
                   {"type": "adjust_standing", "faction": "Independent", "amount": 25},
                   {"type": "adjust_standing", "faction": "Trade Guild", "amount": -10},
                   {"type": "adjust_standing", "faction": "Pirate Territory", "amount": -10},
                   {"type": "flip_region", "from": "Pirate Territory", "faction": "Independent"},
                   {"type": "bump_counter", "name": "story:choice_made"},
               ]),
        Choice("I need more time.", next=None),
    ],
))

_add(Node(
    "hale_after_expose", HALE,
    "It is done. By tomorrow every dock in the sector will know what the "
    "Guild's money has been buying. Some stations are already flying new "
    "colors.\n\n"
    "The Guild will remember your name. Some of its captains will find it "
    "hard to forgive. Mind your back, and come see me about the frontier: "
    "when borders break, someone always moves into the gap.",
    choices=[Choice("Understood.", next=None)],
))

_add(Node(
    "hale_after_join", HALE,
    "So you took Marrow's seat. I will not say I understand it, but I "
    "will say the lanes are already quieter. Guild patrols are pushing out "
    "into the old pirate sectors.\n\n"
    "The independent stations are frightened. Whatever you owe them, owe "
    "them honestly. Come see me about the frontier: not everyone will "
    "accept the new order.",
    choices=[Choice("It is the safest road.", next=None)],
))

_add(Node(
    "hale_after_independent", HALE,
    "A truce. Slow, unglamorous, and the only road that leaves everyone "
    "still standing. Independent space is wider tonight than it was this "
    "morning, and neither the Guild nor the pirates are pleased.\n\n"
    "Come see me about the frontier. A truce is a promise, and somebody "
    "always tests those.",
    choices=[Choice("I expected as much.", next=None)],
))

_add(Node(
    "hale_outpost", HALE,
    "That station at {station:act3_2.a}, the one you pried out of the "
    "warband's hands. It has no owner now, and it would be a shame to let "
    "some other crew move in. Claim it. Call it an outpost, a home port, "
    "whatever you like. It will earn its keep while you fly: %d credits a "
    "minute, up to %d, waiting for you whenever you dock there." % (RATE_PER_MINUTE, CAP),
    choices=[
        Choice("I will claim it.", next="hale_outpost_claimed",
               effects=[{"type": "set_flag", "name": "outpost_claimed"},
                        {"type": "claim_outpost", "mission": "act3_2", "waypoint": "a"}]),
        Choice("Leave it for now.", next=None),
    ],
))

_add(Node(
    "hale_outpost_claimed", HALE,
    "Then it is yours: {station:outpost}. Mind the Guild's tax collectors, "
    "if they come asking. Dock there any time to collect what it has "
    "earned.",
    choices=[Choice("Thank you, Hale.", next=None)],
))

_add(Node(
    "hale_outpost_status", HALE,
    "Your outpost is at {station:outpost}. It earns %d credits a minute "
    "while you play, up to %d. Dock there to collect it." % (RATE_PER_MINUTE, CAP),
    choices=[Choice("Good to know.", next=None)],
))

_add(Node(
    "hale_frontier", HALE,
    "Where borders move, warbands follow. One has taken a station at "
    "{station:act3_2.a} and is bleeding the lanes around it. Break it before "
    "it digs in.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act3_2"}],
    choices=[Choice("I will deal with it.", next=None)],
))

# --- Captain Rourke -------------------------------------------------------------------

_add(Node(
    "rourke_intro", ROURKE,
    "So you are the one flying Jessup's hull. I would know the paint "
    "anywhere. Twenty years we ran lanes together, until he started "
    "keeping secrets and I started pretending not to notice.\n\n"
    "I am Rourke. I have a freighter, a grudge, and fewer friends every "
    "month.",
    on_enter=[{"type": "set_flag", "name": "met_rourke"}],
    choices=[
        Choice("What happened to Vane?", next="rourke_vane"),
        Choice("What do you need?", next="rourke_offer",
               requires={"not_story_started": "act1_1"}),
        Choice("Not now.", next=None),
    ],
))

_add(Node(
    "rourke_vane", ROURKE,
    "Raiders hit his last run an hour out of port. They knew his cargo, his "
    "route and his hour of departure. Nobody finds a lane that precisely by "
    "accident.\n\n"
    "I have had a month of runs hit the same way. Same raiders, same "
    "timing. I cannot afford to lose another hull.",
    choices=[
        Choice("What do you need?", next="rourke_offer",
               requires={"not_story_started": "act1_1"}),
        Choice("I will come back.", next=None),
    ],
))

_add(Node(
    "rourke_offer", ROURKE,
    "I have a freighter of salvage that has to reach {station:act1_1.b}. If "
    "I send it alone it will not arrive, and I have no escort to spare. Fly "
    "with it. Keep it alive. And watch what the raiders do when they see "
    "you.",
    choices=[
        Choice("I will do it.", next="rourke_accept"),
        Choice("Not yet.", next=None),
    ],
))

_add(Node(
    "rourke_accept", ROURKE,
    "The freighter is loaded and waiting. It will leave as soon as you do. "
    "It is bound for {station:act1_1.b}. Fly safe.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act1_1"}],
    choices=[Choice("On my way.", next=None)],
))

_add(Node(
    "rourke_thanks", ROURKE,
    "It arrived. Do you know how long it has been since one of mine "
    "arrived? The raiders were waiting, exactly where Jessup's were, and "
    "they went for the freighter first, not you. They were hunting the "
    "cargo, not the pilot.\n\n"
    "Somebody tells them what moves. I have written down the dates. Take "
    "them to Hale, to your ledger, to anyone who will listen.",
    choices=[Choice("Thank you, Rourke.", next=None)],
))

_add(Node(
    "rourke_return", ROURKE,
    "Captain. Hulls still in one piece?",
    choices=[
        Choice("About that freighter run.", next="rourke_offer",
               requires={"not_story_started": "act1_1", "flag": "met_rourke"}),
        Choice("You said a witness might talk.", next="rourke_witness_offer",
               requires={"story_done": "act2_2", "not_story_started": "act2_3"}),
        Choice("What do you make of the new borders?", next="rourke_borders_expose",
               requires={"flag": "path_expose"}),
        Choice("What do you make of the new borders?", next="rourke_borders_join",
               requires={"flag": "path_join"}),
        Choice("What do you make of the new borders?", next="rourke_borders_independent",
               requires={"flag": "path_independent"}),
        Choice("Just checking in.", next=None),
    ],
))

_add(Node(
    "rourke_witness_offer", ROURKE,
    "There is a clerk, one of the Guild's own, who signed off on the "
    "Hollow payments and has been losing sleep ever since. He will testify "
    "if he reaches {station:act2_3.b} alive. I have him aboard a freighter. "
    "The Guild knows he ran, and it will not let him arrive.",
    choices=[
        Choice("I will get him there.", next="rourke_witness_accept"),
        Choice("Not yet.", next=None),
    ],
))

_add(Node(
    "rourke_witness_accept", ROURKE,
    "Good. The freighter leaves when you do, bound for {station:act2_3.b}. "
    "Expect a heavier welcome than last time.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act2_3"}],
    choices=[Choice("Understood.", next=None)],
))

_add(Node(
    "witness_delivered", "Clerk Dray",
    "I am Anselm Dray. I signed forty-one payments to an account that did "
    "not exist and told myself it was bookkeeping. Then Jessup Vane asked "
    "me where the money went, and a week later he was dead.\n\n"
    "I will say it all, under whatever oath anyone wants. The Hollow "
    "Account, the pirate captains, Director Marrow's mark on every "
    "authorization. You have my statement now, captain. Use it better than "
    "I used my pen.",
    choices=[Choice("It will not be wasted.", next=None)],
))

_add(Node(
    "rourke_borders_expose", ROURKE,
    "Half the Guild's stations are flying other colors and the pirates "
    "lost their paymaster overnight. My runs are the safest they have been "
    "in years. The Guild is not safe to cross, but it is not safe to "
    "trust either. You did that, captain.",
    choices=[Choice("It had to be said out loud.", next=None)],
))

_add(Node(
    "rourke_borders_join", ROURKE,
    "Guild patrols on every lane and my insurance premiums halved. I ought "
    "to thank you. But I have been looking at the contracts they want me "
    "to sign, and I would rather fly into a raider's guns than sign them. "
    "Jessup would not have signed either.",
    choices=[Choice("It is safer this way.", next=None)],
))

_add(Node(
    "rourke_borders_independent", ROURKE,
    "A truce between people who hate each other holds about as well as you "
    "would expect, but independent space is wider and quieter than it has "
    "ever been. I will take slow and honest over fast and bought.",
    choices=[Choice("Slow and honest, then.", next=None)],
))

# --- Auditor Voss --------------------------------------------------------------------

_add(Node(
    "voss_intro", VOSS,
    "Do not say my name too loudly. I am an auditor for the Trade Guild, "
    "which is a polite way of saying I am paid to read what other people "
    "would rather I did not.\n\n"
    "You are flying Jessup Vane's ship. He was one of mine. Not an "
    "employee. An informant, the only kind of friend an auditor can have.",
    on_enter=[{"type": "set_flag", "name": "met_voss"}],
    choices=[
        Choice("What did Vane tell you?", next="voss_vane"),
        Choice("What do you want from me?", next="voss_offer",
               requires={"not_story_started": "act1_2"}),
        Choice("I should go.", next=None),
    ],
))

_add(Node(
    "voss_vane", VOSS,
    "That the Guild's accounts have a hole in them: a monthly payment, "
    "large, to an account with no owner. When he asked who it was for, he "
    "was told to stop asking. A week later his ship drifted home with no "
    "pilot.\n\n"
    "I cannot request records without my own superiors reading the "
    "request. You, on the other hand, are nobody.",
    choices=[
        Choice("What do you want me to fetch?", next="voss_offer",
               requires={"not_story_started": "act1_2"}),
        Choice("I will think about it.", next=None),
    ],
))

_add(Node(
    "voss_offer", VOSS,
    "Manifests filed at a Guild station, {station:act1_2.a}, the week Vane "
    "died. They are public records, technically. In practice nobody gets "
    "them without a reason, and you have a clean standing with the Guild "
    "while I have an audit file with my own name on it.\n\n"
    "Collect them and bring them to me. Do not linger once you have them.",
    choices=[
        Choice("I will collect them.", next="voss_accept"),
        Choice("Not yet.", next=None),
    ],
))

_add(Node(
    "voss_accept", VOSS,
    "Thank you. The manifests are at {station:act1_2.a}. Come straight "
    "back once you have them.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act1_2"}],
    choices=[Choice("On my way.", next=None)],
))

_add(Node(
    "voss_report1", VOSS,
    "Let me see... there. A recurring payment, filed under a code name: the "
    "Hollow Account. Paid monthly, never reported. The payee is never "
    "named, but the amounts match what a dozen pirate captains would "
    "charge to leave honest lanes alone.\n\n"
    "Go to Hale. Tell him the Guild's money is paying the people who rob "
    "the Guild's own traders. He will know what to do with that.",
    on_enter=[{"type": "bump_counter", "name": "story:voss_manifests"}],
    choices=[Choice("I will tell him.", next=None)],
))

_add(Node(
    "voss_return", VOSS,
    "Keep your voice down. What have you got?",
    choices=[
        Choice("I have the manifests.", next="voss_report1",
               requires={"story_stage": ["act1_2", 1]}),
        Choice("About those manifests...", next="voss_offer",
               requires={"not_story_started": "act1_2", "flag": "met_voss"}),
        Choice("Marrow's people want to meet me.", next="voss_offer2",
               requires={"story_done": "act2_3", "not_story_started": "act2_4"}),
        Choice("I met Marrow's man.", next="voss_report2",
               requires={"story_stage": ["act2_4", 1]}),
        Choice("Nothing yet.", next=None),
    ],
))

_add(Node(
    "voss_offer2", VOSS,
    "Marrow knows about the clerk, the ledgers and the receipts. He is "
    "not sending assassins. He is sending an offer. A private meeting at "
    "{station:act2_4.a}, to hear what you want.\n\n"
    "Go. Listen. Say nothing you cannot afford to have repeated. What you "
    "learn will decide what you do with everything else.",
    choices=[
        Choice("I will go.", next="voss_accept2"),
        Choice("Not yet.", next=None),
    ],
))

_add(Node(
    "voss_accept2", VOSS,
    "The meeting is at {station:act2_4.a}. Come straight back and tell me "
    "what was said.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act2_4"}],
    choices=[Choice("Understood.", next=None)],
))

_add(Node(
    "voss_report2", VOSS,
    "He offered you a seat at his table. Of course he did. A galaxy kept "
    "just dangerous enough that every trader needs the Guild's protection "
    "is a very profitable galaxy.\n\n"
    "He is right about the profit and wrong about everything else. Take "
    "all of it to Hale. You will have to choose, and it will not be easy.",
    on_enter=[{"type": "bump_counter", "name": "story:voss_offer"}],
    choices=[Choice("I will choose carefully.", next=None)],
))

# --- Kestrel -----------------------------------------------------------------------------

_add(Node(
    "kestrel_intro", KESTREL,
    "Do not stare at the guns, captain. They are for people who do not "
    "pay. I am Kestrel. I trade in what people know, and half the lanes "
    "have already told me you are flying Jessup Vane's hull.\n\n"
    "Vane paid me well. Better than most, and he never lied about what he "
    "wanted.",
    on_enter=[{"type": "set_flag", "name": "met_kestrel"}],
    choices=[
        Choice("What did Vane buy from you?", next="kestrel_vane"),
        Choice("What do you want?", next="kestrel_offer",
               requires={"not_story_started": "act1_3"}),
        Choice("I am just looking.", next=None),
    ],
))

_add(Node(
    "kestrel_vane", KESTREL,
    "The timing of raids. Which lane, which hour, which captain. He "
    "wanted to know why some convoys were hit and others sailed through. I "
    "told him what I knew, and then I told him what I suspected, and he "
    "stopped coming. Three weeks ago. Now someone else keeps asking about "
    "him, and I do not like the sort of people who ask.",
    choices=[
        Choice("What do you want in return?", next="kestrel_offer",
               requires={"not_story_started": "act1_3"}),
        Choice("I will come back.", next=None),
    ],
))

_add(Node(
    "kestrel_offer", KESTREL,
    "I do not want credits. I want the raiders working the lanes around my "
    "station thinned out: six ships, any six. They are not mine and they "
    "are bad for business. Do that and I will tell you everything.",
    choices=[
        Choice("Six raiders. Done.", next="kestrel_accept"),
        Choice("Not yet.", next=None),
    ],
))

_add(Node(
    "kestrel_accept", KESTREL,
    "Six. Any six. Do not trouble yourself over which. Come back when it is "
    "done and I will keep my word.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act1_3"}],
    choices=[Choice("I will be back.", next=None)],
))

_add(Node(
    "kestrel_report1", KESTREL,
    "The lanes are quiet. Good. A deal is a deal.\n\n"
    "Every captain in this region is paid on the first of the month, in "
    "clean credits, by someone nobody has ever seen. When the payments "
    "are late, the raids slow down. When they arrive, the raids come back "
    "worse. I did not understand why anyone would pay people to rob their "
    "own side. Now I think I do, and so do you.",
    on_enter=[{"type": "bump_counter", "name": "story:kestrel_favor"}],
    choices=[Choice("Thank you, Kestrel.", next=None)],
))

_add(Node(
    "kestrel_return", KESTREL,
    "Still alive. I am almost impressed. What can I do for you?",
    choices=[
        Choice("The lanes are clear now.", next="kestrel_report1",
               requires={"story_stage": ["act1_3", 1]}),
        Choice("About that favor...", next="kestrel_offer",
               requires={"not_story_started": "act1_3", "flag": "met_kestrel"}),
        Choice("Tell me about the Hollow Account.", next="kestrel_paymaster",
               requires={"story_done": "act2_1", "not_story_started": "act2_2"}),
        Choice("I have Dross's receipts.", next="kestrel_report2",
               requires={"story_stage": ["act2_2", 1]}),
        Choice("What do you make of the new borders?", next="kestrel_borders",
               requires={"flag": "path_chosen"}),
        Choice("Nothing. Goodbye.", next=None),
    ],
))

_add(Node(
    "kestrel_paymaster", KESTREL,
    "The Hollow Account pays ten captains. One of them, Dross, is the "
    "paymaster: he carries the receipts himself because he does not trust "
    "anyone else to count. He is holed up near {station:act2_2.a} with a "
    "heavy and two fighters.\n\n"
    "I want him gone. You want what he carries. Between us we want the "
    "same thing.",
    choices=[
        Choice("I will take him.", next="kestrel_accept2"),
        Choice("Not yet.", next=None),
    ],
))

_add(Node(
    "kestrel_accept2", KESTREL,
    "He is near {station:act2_2.a}. When he is dead, bring me whatever he "
    "was carrying. I will tell you what it means.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act2_2"}],
    choices=[Choice("Consider him dead.", next=None)],
))

_add(Node(
    "kestrel_report2", KESTREL,
    "Dross, finished. Good. And this is every receipt he ever signed for. "
    "Look at the mark on the authorizations: the same hand on every one. "
    "Director Marrow of the Trade Guild.\n\n"
    "You have it now, captain. The proof I could never have taken to "
    "anyone, because nobody believes a pirate broker.",
    on_enter=[{"type": "bump_counter", "name": "story:paymaster_receipts"}],
    choices=[Choice("They will believe it now.", next=None)],
))

_add(Node(
    "kestrel_borders", KESTREL,
    "Borders move, and business moves with them. Whoever drew the old "
    "lines is not drawing the new ones. I trade in what people know and "
    "right now everyone knows less than they think. Come back when you "
    "have something I can use.",
    choices=[Choice("I will.", next=None)],
))

# --- The Archivist -------------------------------------------------------------------------

_add(Node(
    "archivist_intro", ARCHIVIST,
    "Records are a kind of silence, captain. Nobody looks at them until "
    "they need them, and by then it is usually too late. I have read every "
    "ledger the Guild keeps for thirty years. I know what was paid, to "
    "whom, and under which name.\n\n"
    "Jessup Vane came to see me once. He asked a very good question. I "
    "should have answered it.",
    on_enter=[{"type": "set_flag", "name": "met_archivist"}],
    choices=[
        Choice("What was the question?", next="archivist_question"),
        Choice("What can you tell me now?", next="archivist_offer",
               requires={"not_story_started": "act2_1"}),
        Choice("I will come back.", next=None),
    ],
))

_add(Node(
    "archivist_question", ARCHIVIST,
    "He asked where the Hollow Account's money goes. I said I did not "
    "know. That was a lie by omission: I knew where the ledgers were. I "
    "simply did not dare read them.\n\n"
    "He is dead, and I am still afraid, but I am more afraid of becoming "
    "the man who did nothing.",
    choices=[
        Choice("Help me now.", next="archivist_offer",
               requires={"not_story_started": "act2_1"}),
        Choice("I will be back.", next=None),
    ],
))

_add(Node(
    "archivist_offer", ARCHIVIST,
    "The sealed ledgers are kept at {station:act2_1.a}. I have copied what "
    "I could into a case there under an old requisition. I cannot carry "
    "it out, because every door I pass is logged. Anyone else could. "
    "Collect it and bring it to me, and I will read you what it says.",
    choices=[
        Choice("I will fetch the case.", next="archivist_accept"),
        Choice("Not yet.", next=None),
    ],
))

_add(Node(
    "archivist_accept", ARCHIVIST,
    "The case is at {station:act2_1.a}, marked as routine supplies. Take "
    "nothing else and speak to no one.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act2_1"}],
    choices=[Choice("Understood.", next=None)],
))

_add(Node(
    "archivist_report", ARCHIVIST,
    "Yes. These are the ones. Ten captains, one account, paid on the same "
    "day each month. And look here: the payments rise whenever the "
    "Guild's insurance premiums are due for renewal, and fall afterward.\n\n"
    "It is not charity and it is not an accident. The Guild pays pirates "
    "to keep every lane it does not control frightening enough that "
    "traders pay for protection. I knew it. I have known it for years.",
    on_enter=[{"type": "bump_counter", "name": "story:archivist_papers"}],
    choices=[Choice("Thank you. I will use it.", next=None)],
))

_add(Node(
    "archivist_return", ARCHIVIST,
    "The silence is a kind of company. What brings you?",
    choices=[
        Choice("I have the copied ledgers.", next="archivist_report",
               requires={"story_stage": ["act2_1", 1]}),
        Choice("About the sealed ledgers...", next="archivist_offer",
               requires={"not_story_started": "act2_1", "flag": "met_archivist"}),
        Choice("Just visiting.", next=None),
    ],
))

# --- Dr. Okoye ---------------------------------------------------------------------------------

_add(Node(
    "okoye_intro", OKOYE,
    "You are the one with Jessup Vane's ledger. Good. I have been hoping "
    "someone would bring it to me.\n\n"
    "I listen to the dark between stations, captain. For eleven years I "
    "have been recording a signal nobody else seems to hear: faint, "
    "repeating, patient. Vane sent me a recording of it once, and a page "
    "of his shorthand. I could not read the page. I think you can help.",
    on_enter=[{"type": "set_flag", "name": "met_okoye"}],
    choices=[
        Choice("Tell me about the signal.", next="okoye_signal"),
        Choice("What do you need?", next="okoye_offer",
               requires={"story_done": "act3_2", "not_story_started": "act3_3"}),
        Choice("What do you need?", next="okoye_not_yet",
               requires={"not_story_started": "act3_2"}),
        Choice("Another time.", next=None),
    ],
))

_add(Node(
    "okoye_signal", OKOYE,
    "It repeats every nineteen hours. It does not carry words, but it "
    "carries structure: nested, ordered, like a chart. Whoever or "
    "whatever sends it has been sending the same message since before any "
    "faction existed.\n\n"
    "And someone has spent a great deal of money making sure traders "
    "never get close enough to hear it clearly.",
    choices=[
        Choice("What do you need from me?", next="okoye_offer",
               requires={"story_done": "act3_2", "not_story_started": "act3_3"}),
        Choice("What do you need from me?", next="okoye_not_yet",
               requires={"not_story_started": "act3_2"}),
        Choice("I will come back.", next=None),
    ],
))

_add(Node(
    "okoye_not_yet", OKOYE,
    "The frontier is too unsettled for my work. Warbands are raiding every "
    "station within reach of my instruments. When the one nearest has been "
    "broken, come and see me. Hale will know where it is.",
    choices=[Choice("I will deal with it.", next=None)],
))

_add(Node(
    "okoye_offer", OKOYE,
    "My instruments are not sharp enough to decode Vane's page. There is "
    "an array at {station:act3_3.a} that can calibrate them: dock there, "
    "run the sequence I will give you, and bring the results back to me.",
    choices=[
        Choice("I will calibrate the array.", next="okoye_accept3"),
        Choice("Not yet.", next=None),
    ],
))

_add(Node(
    "okoye_accept3", OKOYE,
    "The array is at {station:act3_3.a}. Dock, run the sequence, and come "
    "straight back. It should take no more than an hour.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act3_3"}],
    choices=[Choice("On my way.", next=None)],
))

_add(Node(
    "okoye_report3", OKOYE,
    "The calibration is perfect. Give me a moment... there. Vane's page "
    "was not an account at all. It is a position, and a note: every "
    "captain on the Hollow Account sits on a lane that leads there. The "
    "money was never about prices. It buys silence about what is out "
    "there.\n\n"
    "The source of the Signal. That is where Jessup was going. That is "
    "where someone did not want him to arrive.",
    on_enter=[{"type": "bump_counter", "name": "story:okoye_calibrated"}],
    choices=[Choice("Then we go there.", next=None)],
))

_add(Node(
    "okoye_return", OKOYE,
    "Captain. The sky is a little less quiet because of you.",
    choices=[
        Choice("The array is calibrated.", next="okoye_report3",
               requires={"story_stage": ["act3_3", 1]}),
        Choice("About that calibration...", next="okoye_offer",
               requires={"story_done": "act3_2", "not_story_started": "act3_3",
                         "flag": "met_okoye"}),
        Choice("What did the decoded page say?", next="okoye_plan",
               requires={"story_done": "act3_3", "not_story_started": "act4_1"}),
        Choice("I have earned my captain's rank.", next="okoye_ready",
               requires={"story_stage": ["act4_1", 1]}),
        Choice("Where was it again?", next="okoye_coords",
               requires={"story_done": "act4_1", "not_story_started": "act4_2"}),
        Choice("Remind me where to go.", next="okoye_coords_again",
               requires={"story_active": "act4_2"}),
        Choice("The new borders worry me.", next="okoye_borders_expose",
               requires={"flag": "path_expose"}),
        Choice("The new borders worry me.", next="okoye_borders_join",
               requires={"flag": "path_join"}),
        Choice("The new borders worry me.", next="okoye_borders_independent",
               requires={"flag": "path_independent"}),
        Choice("Just checking in.", next=None),
    ],
))

_add(Node(
    "okoye_plan", OKOYE,
    "The Signal's source is beyond anything charted. The fleet that "
    "guards it will not be like the raiders you have met. I will not send "
    "an unproven pilot out there.\n\n"
    "Earn the rank of Captain. Come back when you have, and I will give "
    "you the coordinates.",
    on_enter=[{"type": "start_story_mission", "mission_id": "act4_1"}],
    choices=[Choice("I will earn it.", next=None)],
))

_add(Node(
    "okoye_ready", OKOYE,
    "A captain. Then you are as ready as anyone can be. I have decoded "
    "the position as far as I can.",
    on_enter=[{"type": "bump_counter", "name": "story:okoye_ready"}],
    choices=[Choice("Give it to me.", next="okoye_coords")],
))

_add(Node(
    "okoye_coords", OKOYE,
    "The position is Sector (%d, %d), well past the last charted station. "
    "I will keep listening from here. When you arrive, you will know. The "
    "Signal grows louder, and so will whatever is guarding it." % SIGNAL_SECTOR,
    on_enter=[{"type": "start_story_mission", "mission_id": "act4_2"}],
    choices=[Choice("I will find it.", next=None)],
))

_add(Node(
    "okoye_coords_again", OKOYE,
    "Sector (%d, %d). Fly out past the last station and watch your "
    "Navigation display. The Signal grows louder as you close." % SIGNAL_SECTOR,
    choices=[Choice("Thank you.", next=None)],
))

_add(Node(
    "okoye_borders_expose", OKOYE,
    "You tore the Guild open and the pirates lost their paymaster. It was "
    "brave and it was loud. Every faction is looking at the frontier now, "
    "which means the Signal will not stay secret for long.",
    choices=[Choice("Then we are out of time.", next=None)],
))

_add(Node(
    "okoye_borders_join", OKOYE,
    "The Guild owns more lanes than ever, and I notice it is also asking "
    "very pointed questions about my instruments. Marrow wants the Signal "
    "as much as anyone. Do not let him have it by default.",
    choices=[Choice("I will not.", next=None)],
))

_add(Node(
    "okoye_borders_independent", OKOYE,
    "A fragile peace, and independent space is wider for it. If the "
    "Signal proves to be what I think it is, a fragile peace may be all we "
    "have to meet it with.",
    choices=[Choice("It will have to do.", next=None)],
))

# --- Scenes ------------------------------------------------------------------------------------

_add(Node(
    "signal_arrival", OKOYE,
    "Captain, can you hear it? Through the relay I can: the Signal, "
    "louder than I have ever heard it, and under it something moving. "
    "There is a fleet ahead of you, holding station around the source.\n\n"
    "Whoever has been paying for silence kept a force here. Be careful.",
    choices=[Choice("I am going in.", next=None)],
))

_add(Node(
    "signal_choice", "The Signal",
    "With the guarding fleet broken, the transmission resolves into "
    "something you can see: a chart. Lanes, stations, whole sectors, "
    "laid out beyond anything the Guild ever mapped, and at its center "
    "a marker that reads, as plainly as a signpost, 'Come in.'\n\n"
    "Whoever left it left it for anyone. Now it is yours to decide what "
    "anyone means.",
    choices=[
        Choice("Open the Signal to every faction.", next=None,
               effects=[{"type": "set_flag", "name": "signal_open"},
                        {"type": "complete_campaign"}]),
        Choice("Seal it until we understand it.", next=None,
               effects=[{"type": "set_flag", "name": "signal_sealed"},
                        {"type": "complete_campaign"}]),
    ],
))
