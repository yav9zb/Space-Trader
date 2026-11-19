# Changelog

## Beta 14

### Fixed
- **The mission tracker now follows the current step.** A story mission's tracker entry used to point at its first station forever. It now points at wherever the current step happens (a station, the contact to report back to, or a sector) and shows its coordinates.
- **The mission tracker no longer covers the minimap.** Both sit in the top-right corner; the tracker now sits below the minimap.
- **Docs and the first-flight hint claimed docking was fully manual.** Approaching a station slowly docks automatically; the dock key is a manual shortcut.

## Beta 13

### Added
- **The full campaign.** The story now runs from the prologue through four acts, 16 story missions in all, told through six contacts you find at stations:
  - **Act 1, The Ledger:** Captain Rourke, Auditor Voss of the Trade Guild and Kestrel, a broker in Pirate Territory, each hold a piece of what Jessup Vane found. Hale ties it together.
  - **Act 2, The Guild's Secret:** the Archivist copies the Guild's sealed ledgers, you hunt down the pirate paymaster Dross, escort a witness to safety, and hear what Director Marrow has to offer.
  - **Act 3, Border War:** you choose what to do with the evidence. Expose the Guild, accept Marrow's offer, or broker a truce. Each choice moves faction standing and redraws the borders differently, and the frontier warbands that follow must be broken.
  - **Act 4, The Signal:** Dr. Okoye decodes Vane's last page. Earn the rank of Captain, fly to a sector far past the charted stations, and break the fleet guarding the source.
- **Six endings.** The ending depends on the path you took in Act 3 and on whether you open or seal the Signal. The ending screen shows a summary of your run.
- **New Game+.** After the ending you can start a new game with one legacy perk: Veteran's Name (15 reputation), Old Money (20% more credits) or Friends in Every Port (+10 standing with every faction). The perk is kept in its own file, applies once, and survives restarts.
- **New mission steps for the story:** destroy a named fleet at a station or in a sector, escort a trader past an ambush, and reach a far sector. Fleets and escorted traders come back as needed after loading a save.
- The Logbook shows what to do next when an act's missions are all done, and lists every ledger entry you uncover.
- **Achievements.** 18 achievements, from your first pirate kill to seeing all six endings, are tracked across games and shown in a new Logbook page. Each unlock is announced on screen and passed to Steam when Steam is running (the Steam side is untested without the SDK).

### Fixed
- **Starting a new game kept your old ship.** Credits, cargo and upgrades carried over from the previous game, and ships from the old universe stayed in the world. A new game now starts with a fresh ship in a clean universe.
- Story missions that depend on your rank now read the same reputation the rest of the game uses.

## Beta 12

### Added
- **Liberation missions** (Military Bases, reputation 20). A pirate stronghold sits at the heart of a Pirate Territory region: a Warlord, two heavy raiders and two fighters. Destroy all five and the region becomes Independent space. The Trade Guild's patrols leave the stronghold to you. If you save and reload mid-mission, only the surviving ships come back.
- **Borders that move.** Control of a region can now change for good. Prices, patrol and bandit traffic, station factions and the HUD all follow the new owner, the change is announced on screen, and it is saved with the game. The starting area can never change hands. Systems already generated keep the ships and stations they had.
- Story dialogue can now flip the nearest region of a faction (the `flip_region` effect), ready for the campaign's later acts.

## Beta 11

### Added
- **Smuggling.** Military goods (laser cells, plasma cartridges, missiles, railgun slugs) are contraband in Trade Guild space. Docking at a Guild station while carrying any risks an inspection: the cargo is seized, you are fined half its value, your Guild standing drops, and a mission carrying it fails. The risk is 60%; it halves once the Guild favors you (standing 25+) and disappears at 60+. Pirate stations pay a 60% premium for the same goods.
- **Smuggling Run missions** (Mining Stations and Shipyards): deliver contraband, usually to a Pirate station, for about double the usual pay. Avoid Guild stations on the way.
- **Market events.** Every few minutes near you, a pirate raid raises prices in a region, a shortage spikes one commodity, or the Trade Guild embargoes one (it disappears from that region's markets). Each lasts ten minutes and appears as "Market news" on screen and in the Logbook's Factions page.

### Fixed
- **Markets never recovered.** Station stock and demand were only ever depleted by trading and never restored, and prices never moved. Markets now refresh every 30 seconds of play.

## Beta 10

### Added
- **Escort missions.** Guard a trader on its run to another station. It is spawned when you accept, with a pirate ambush waiting beside the route. Pirates now go after an escorted trader if it is closer than you are. The mission succeeds if the trader docks and fails if it is destroyed. Escorted traders never flee, so they keep heading for their destination. Offered at Trading Posts and Mining Stations.
- **Bounty missions.** Hunt a named pirate captain (shown with a name label) in a given sector, usually in Pirate Territory. Heavier captains lurk farther out. Offered at Military Bases and Shipyards.

- **Trade Guild patrols.** Armed patrols now roam Trade Guild space, hunt bandits they can see (but leave bounty targets for you), and are attacked by bandits in turn.
- **Call for backup.** At Captain rank, press H to call two Trade Guild patrols to your position for 90 seconds (3 minute cooldown). The Guild won't answer if it is hostile to you.
- **Consequences for making enemies.** When your standing with a faction drops to -60 it becomes hostile: Trade Guild and Pirate stations refuse you docking, and Guild patrols attack you on sight. Independent stations always let you dock, so you can always trade your way back. Firing on a patrol costs standing (more if you destroy it) and provokes it for two minutes.
- **Ways back from hostile.** Destroying bandits in Trade Guild or Independent space earns +2 standing with that faction, and negative standing slowly cools off by one point per minute of play.
- **On-screen notifications** for events like calling backup.

### Fixed
- **Most mission types could not be accepted, even with enough reputation.** Supply runs (reputation 5), trading contracts (10), exploration (15), and emergency deliveries (20) passed the reputation check, then failed a second check that ignored your reputation and reported "Failed to accept mission". Only reputation-free missions could be taken. Reputation-gated missions now accept normally.

## Beta 9

### Added
- **The prologue.** Talk to Dock Master Hale to begin a three-mission opening chapter: earn a trader's license, find what Jessup Vane left in a rented berth, and meet the courier he trusted. Story missions appear in the Active tab of the Mission Board, show their current step in the Logbook, and are saved with the game. Abandoning one just lets you pick it up again from Hale.
- **Story scenes** play automatically when you finish certain missions, and each step adds an entry to the ledger in your Logbook.


### Fixed
- **Loaded games showed stations with a random look.** Stations kept their type, name and market after a load but came back with a random shape and color. They now look the way they did when you saved.

## Beta 8

### Added
- **Station contacts and conversations** - named characters can wait at stations. When docked at one you will see a prompt; press the Talk key (N with WASD controls, Z with arrow-key controls) to start a conversation. Your first contact is Dock Master Hale, at a nearby Independent station.
- **Logbook** - new pause menu entry with three pages: Story (current chapter and decoded ledger entries), Contacts (who you have met and where), and Factions (your standing with each).
- **Prologue** - the opening conversation with Hale. The rest of the campaign follows in later betas.

### Fixed
- **Arrow-key (left-handed) controls: you could not undock.** Dock and Trading shared F, and Undock and Upgrades shared G, so the first matching action always won. Station services now use Z/X/C/V (talk, trading, upgrades, missions); F/G remain dock/undock. WASD controls are unchanged apart from the new Talk key (N). A test now prevents two actions from ever sharing a key.

## Beta 7

### Fixed
- **Accepted missions could never be completed after loading a save.** Saves rebuilt every mission as a plain base mission, dropping the type-specific progress logic and state (cargo pickup status, exploration progress, and so on). Mission types and their state now survive save/load; older saves still load.

### Internal
- Groundwork for a story campaign: persistent campaign state saved alongside the game, event tracking (docking, kills, mission completions), a dialogue engine, and a conversation screen. No player-visible story content yet.

## Beta 6

### Added
- **Faction-gated missions** - missions can require a minimum standing with whoever's territory issued them.
- **Faction-based upgrade pricing** - standing with a station's controlling faction discounts (trusted) or marks up (hostile) upgrade prices, stacking with the existing station-type discounts.

### Fixed
- Recovered some vertical space in the Mission Board details view as a partial mitigation for content clipping (a fuller fix is tracked separately).

## Beta 5

### Added
- **Per-faction reputation** - standing with Trade Guild, Independent, and Pirate Territory tracked separately from overall reputation. Missions build or damage standing with the faction that issued them; attacking a trader hurts standing with that trader's faction specifically.

## Beta 4

### Added
- **Neutral trader NPCs** - unarmed ships that fly between stations and flee if attacked.
- **Faction-controlled sectors** - Trade Guild, Independent, and Pirate Territory zones (deterministic per seed, shown in the Navigation HUD) with different trader and bandit density. The starting area is always safe.
- **Piracy has a cost** - attacking traders plunders credits but costs reputation.

## Beta 3

### Added
- **Display settings submenu** - Resolution (Windowed mode), Display Mode (Windowed/Fullscreen/Borderless), and HUD Scale (0.75x-1.75x). Added in response to feedback that some HUD text was hard to read.
- **Reputation system** - missions have required a minimum reputation since before beta 1, but reputation was never tracked, so those missions were permanently unacceptable. Now tracked, saved, and shown in the HUD and Mission Board.
- **Rank/License progression** - reputation maps to ranks (Rookie, Trader, Merchant, Captain, Legend); the top tier of ship upgrades requires Captain rank.

## Beta 2

### Fixed
- **Flight view could go blank** - `PlayingState.render()` only drew the starfield and stations, then returned; the rest of the draw calls (ship, planets, debris, combat effects, minimap, HUD, onboarding hints) were misplaced inside a helper that only ran when a station was on screen. Flying far enough from every station left nothing but stars visible. Found via playtesting; fixed by restoring those draw calls to `render()` so they always run.

## Beta 1

First public beta. The core game (movement, procedural universe, docking,
trading, missions, combat, upgrades, base building, save/load) already
existed going into this pass; this release is the work to take it from
"functional" to "ready for outside testers."

### Added
- **Difficulty Levels** - Peaceful, Easy, Normal, Hard, Extreme. Affects hazard frequency, enemy spawns, damage taken, mission rewards/time limits, repair/upgrade costs. Extreme adds permadeath.
- **Audio** - sound effects (weapons, explosions, docking, engines, UI) and music stingers, with working Master/SFX/Music volume controls. Previously the game was completely silent.
- **First-time onboarding hints** - a brief, dismissible flight-controls hint on first launch and a station-services hint on first dock, shown once ever.
- **App icon**, for both the packaged build and the in-game window.
- **Full visual pass** - redesigned ship, bandit ships, weapon projectiles, and explosion effects; fixed stations and gas giant planets (see Fixed, below) and gave every station type and planet type a distinct look; consistent starfield-background/accent-panel styling across every menu screen (previously only some screens had any visual polish).
- **Standalone packaging** - a PyInstaller build (verified on macOS; Windows/Linux via CI, not yet verified) and a GitHub Actions workflow that builds all three platforms on a version tag.
- **Steam integration scaffolding** - unverified against a real Steamworks SDK (see `STEAM_RELEASE_CHECKLIST.md`), but wired in and safe to ship as a no-op without it.

### Fixed
Found by actually rendering and testing the game, not just reading the code:
- **Severe frame rate drop** (~15fps) from unbounded collision-spark accumulation in the debris system - capped, restoring ~65fps+.
- **Stations always rendered as plain circles** regardless of type - a same-size filled circle was drawn directly on top of the type-specific shape (octagon, triangle, etc.) every time, completely hiding it.
- **Gas giant cloud bands ignored the planet's circular edge**, sticking out as flat rectangular bars instead of following the sphere.
- **Ice/lava planet surface details re-randomized every single frame** instead of being stable, which would look like flickering noise rather than a surface.
- **A dead stub class silently shadowed the real `GameOverState`** - dying on Extreme difficulty (permadeath) showed a black screen with no way back to the menu.
- Several screens' content could overflow into fixed-position footer text (Trading's commodity list, Mission Board's list and details view, Load Game's save list) - added scrolling/clipping.
- Multiple UI strings used Unicode glyphs (arrows, checkmarks, bullets, a pointer character) that pygame's default font can't render, showing as empty boxes - replaced with plain text/ASCII equivalents.
- World-seed determinism relied on Python's `hash()`, which is randomized per process - the "same" seed could generate different content across separate game launches. Switched to `zlib.crc32`.
- New games could plausibly spawn with no station anywhere nearby, depending on random universe generation - now guaranteed.
- `settings.json`/save files/logs used paths relative to the working directory, which breaks in a packaged app (a signed macOS `.app` is read-only; the working directory on launch isn't predictable). Now resolved to an OS-appropriate per-user data directory when running as a packaged build.

### Changed
- Repo hygiene: removed an accidentally-tracked `node_modules/` and tracked `__pycache__` files, stopped tracking personal runtime state (`settings.json`, `saves/`), populated `requirements.txt` (was empty).
- Dropped an unbacked MIT license claim in favor of an explicit "all rights reserved" note, since this is being prepared for a possible paid release.
- Consolidated and fixed several broken/duplicated ad-hoc test scripts that lived at the repo root instead of in `tests/`.
- All `.md` documentation reviewed and corrected against the actual implementation - several docs had stale key bindings, references to files that don't exist (early planning docs written before implementation settled on a different file layout), and roadmap items describing already-shipped features as "planned."

### Known limitations (see README's "Known Issues" section for the live list)
- No automated test coverage for the save system specifically.
- Display settings (resolution/fullscreen) aren't configurable in-game yet.
- No auto-dock.
