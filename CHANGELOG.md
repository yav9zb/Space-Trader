# Changelog

## Beta 25

### Added
- **Raids, and turrets to stop them.** Pirates now come for a base that has something built, every ten to fifteen minutes. Bigger bases draw bigger raids, from two scouts up to a boss with escorts.
  - If you are near, the raiders are real ships: they fly in, aim at the base, and shoot its modules. Anything knocked out stops working (a generator stops powering, storage stops holding) and mends by itself once the shooting stops. Raiders that find you close to the base fight you too, and they do not run when hurt.
  - **Turret** (key 6 in the build list, 2,500 credits plus 2 machinery and 2 electronics): a base turret that shoots raiders in range, leading moving ships. It needs power (at least half of full power to fire). Turrets do not pay a bounty, count toward your kills or touch bounty targets, which stay yours to collect.
  - If you are away, the raid is settled on numbers: each working turret stands against a share of the raid. Enough turrets and nothing is lost; too few and goods are stolen (up to 30 percent of each stock) and modules are knocked out. Fly far away in the middle of a raid and the rest of it is settled the same way. Raiders that have not won after four minutes give up.
  - The base screen shows your turrets, your defense against the next raid's strength, and anything knocked out, with an UNDER ATTACK line during a raid. You are told when a raid starts and how it ended. Raid countdowns and module damage are saved.

### Fixed
- **A base factory lost money.** It turned 2 electronics and 1 metal ore (worth 700) into 1 machinery (worth 400). It now makes 2 machinery from the same inputs. A test now checks that no recipe makes goods worth less than it uses.
- **Boxes behind text on Retina Macs.** The sharp-pixel path scaled the world onto a surface whose transparency was left at zero, and text drawn over it then took its own colour for the whole rectangle around each letter instead of blending. Headings, tabs and key hints over the world could show a pale box behind them. The surface is now made opaque after the world is scaled onto it, in the flight path and in the base screen.

## Beta 24

### Added
- **Bases you can actually build.** Press B in open space, away from stations, and found a base for 4,000 credits (up to three). It starts with a command center and a starter kit of goods.
  - Build power generators, storage, mining facilities, refineries and factories. You pay in credits from your ship and goods taken from the base's own storage, so you haul supplies there. Modules take time to build and need power; with too little power everything slows down in proportion.
  - Modules run by themselves: a mining facility digs up metal ore, a refinery turns 2 ore into electronics, a factory turns electronics and ore into machinery. Production waits when storage is full. Bases keep working wherever you are, including while you are docked or in a menu.
  - The **Storage** tab moves goods between your hold and the base (mission cargo stays with you). The **Production** tab shows what each module is doing. Clicking a module in the list, or pressing 1 to 5, chooses what to build, and clicking the grid builds it. Remove mode (R) takes a module down and refunds half.
  - Bases are drawn in flight, appear on the radar, say so when you come within reach, and are saved with the game. Starting a new game clears them.
- The old base code (14 module types, costs of 50,000 credits for a command center, and a command center that could never be built) was replaced: nothing in it fitted the game's economy.

## Beta 23

### Added
- **Docking settings** (Settings > Docking). Turn Auto-Docking off to dock only when you press the dock key, and set the docking speed limit to Careful (30), Standard (50, as before) or Relaxed (80). Both are saved and apply at once. With auto-docking off, the "ready to dock" prompt now names the key you actually have bound (it always said D).

### Changed
- **The base construction screen (B) was rebuilt like the other menus.** Its tabs, panels, help and status line fit the window, are drawn at the screen's real pixels, and the tabs can be clicked (Q, W and E still work). The base is centred in the view, and the mouse now lines up with the grid at any zoom. Escape leaves in one press (it used to switch construction off first and leave a blank screen), and with no base it says so instead of showing an empty screen. Nothing in a run creates a base yet, so for now that is what you will see.

## Beta 22

### Fixed
- **Flight is smoother, especially on Retina Macs.** In a real Retina window flight ran at about 43 frames a second and now holds 60. Three causes:
  - Debris physics did its neighbour search and gravity with a vector object per pair of pieces. It now uses plain numbers, and only simulates in full the debris near what the window can show (a little beyond its edge, so a bigger window sees further), the rest updating every fourth frame.
  - Pulsing glows (explosive and radioactive asteroids, station lights) built a new cached image almost every frame. Sizes and colours are now rounded to nearby steps, so a handful of images are reused. The difference is not visible.
  - The first-time hints loaded their font and redrew their text every frame they were on screen. They are now drawn once.

## Beta 21

### Changed
- **Moved from pygame to pygame-ce** (a drop-in fork; the install line is the only change for you: run `pip install -r requirements.txt`).
- **Sharp HUD on Retina Macs.** On a high-density display the HUD panels, radar, mission tracker and notifications are drawn at the screen's full pixel resolution. The world is still drawn at point resolution and scaled up, so it looks as before. Standard displays, headless runs and `SPACETRADER_HIDPI=0` use the plain path.
- **Every menu screen was rebuilt to fit the window.** The main menu, pause menu, game over, Save, Load, Trading, Ship Upgrades, Settings, Mission Board, dialogue, logbook and ending screens measure themselves from the window size instead of being drawn on a fixed grid and enlarged. Text is drawn at the screen's real pixels, so it is sharp on Retina displays, and big windows get bigger text and roomier layouts instead of a small picture in a corner. Everything fits from 1024x640 up to ultrawide.
  - Trading, Ship Upgrades and the Mission Board have clickable rows, tabs and Buy / Sell / Accept / Leave buttons next to the keys.
  - Settings is one page per category with a value on each row (click the left or right half of a row to lower or raise it), and the Controls and Help pages show a reference panel beside the list.
  - Mission details wrap and scroll, so a long briefing is no longer cut off at the bottom of the panel.
  - Load and Save lists scroll and can be clicked.

### Fixed
- **Debris simulation was the biggest cost of every frame.** Up to 500 pieces collided and attracted each other every frame, even far from the player. Pieces beyond 2,500 units now update every fourth frame with the time they missed. Update time dropped from about 13 ms to about 7 ms in a headless run.

## Beta 20

### Changed
- **A better player ship.** Swept wings, engine pods that glow, a canopy with a highlight, and shading that reads as lit from the left.
- **A proper cloaking shimmer.** Cloaked, your ship is surrounded by a cool pulsing glow, two ripples spreading outward, and flecks of bent light orbiting the hull.
- **Screens fade in** over a fifth of a second when you move between menus, trading and the like. Flight and its pause menu still swap instantly.
- **Rewards pop up where they happen.** Destroying a pirate shows "+N cr" rising from the wreck.

### Fixed
- The Ship Upgrades screen no longer overlaps its own help text on small windows (the scaled layouts from beta 19 give it room).

## Beta 19

### Changed
- **Built for the whole range of Mac displays.** Window sizes are now worked out in points, the way macOS counts them, so a 14-inch MacBook Pro is treated as the 1512x982 screen it presents rather than its 3024x1964 pixels.
  - The first window is sized to the screen (about 80% of what is left under the menu bar and Dock, in a 16:10 shape) instead of a fixed 1280x720.
  - A window size saved on a bigger monitor is pulled back onto the screen you are on now, and never goes below 1024x640.
  - The resolution list in Settings only offers sizes that fit. It used to list physical-pixel sizes on a Retina Mac, which were twice as wide as the screen. Stepping the resolution from a window you dragged to an odd size now goes to the next listed size.
  - Resizing the window no longer re-creates it on every event, which flickered and fought macOS's own fullscreen (the green button). The layout simply follows the new size.
  - "Fullscreen" and "Borderless" on a Mac now fill the whole usable screen rather than a window 50 pixels short of it, and leave your windowed size alone.
- **Menus, trading, upgrades, missions, settings, the logbook, conversations and the ending adapt to the window.** They are laid out for a fixed height, so on a short window the Settings list ran off the bottom, and on a big one the text sat tiny in a corner. They are now drawn at a size suited to their layout and scaled to fill the window (down to 1024x640, and up to 2560x1440 and beyond), with the mouse mapped accordingly. The pause menu is scaled the same way over the unscaled game. Flight and the HUD are still drawn at the window's real pixels.
- The starfield has more stars on bigger windows.

### Known limits
- pygame 2.6 draws at point resolution and macOS enlarges the picture on Retina screens, so the game is sized correctly but not drawn at the screen's full pixel density.

## Beta 18

### Changed
- **The HUD panels were rebuilt.** Ship Status and Navigation now size themselves to their content, so there is no dead space and nothing spills past a border, and they stack with a constant gap. Hull, cargo and fuel are bars with the value written on them, turning amber and then red as they run low. Ammo is a row of four small gauges. Speed, afterburner, rank, faction and docking status each have their own line, and the afterburner, faction and docking status are coloured tags. When the window is too short for the full panels, a compact version drops the lowest-priority lines instead of running off the bottom.
- **The minimap is now a radar.** It is round, with range rings and a crosshair, and your ship is a wedge that turns with your heading. Stations are squares, planets are coloured circles, hostile ships are red triangles, patrols blue, traders grey, radioactive and explosive asteroids green and orange, black holes purple, and mission objectives gold diamonds. An objective beyond the range is pinned to the rim with an arrow. The range is written under the radar instead of over it, and the radar grows with the window.
- **The mission tracker** uses the same style, truncates long titles instead of overflowing, shows time remaining and coordinates, and sits below the radar. The objective arrow's label is drawn underneath the panels, not over them.
- HUD text sizes now scale with the window. At small windows the old sizing made the new font about 8 pixels tall.

### Fixed
- **Running the tests rewrote your real `settings.json`.** The settings were loaded and saved at import time, so every test run overwrote them with test-environment values (a 700x500 window, hints marked as seen). All user-data paths are now redirected to a temporary folder for the whole test suite. If your window size or hints look wrong, that is the cause.

## Beta 17

### Changed
- **More visual polish.** Asteroids are lit, cratered rocks, with a pulsing green radiation glow on radioactive ones and a hot flickering glow on explosive ones. Black holes have a violet lensing glow, an orange accretion ring, a bright photon ring and a black core. Weapon shots have glows and tails and are colour-coded by who fired them: blue for you, green for patrols, red for everyone else. Missiles have a real exhaust flame. Status bars (HUD, mission progress, enemy and asteroid health) are lit bars with a trough, and a nearly empty bar pulses red. HUD and menu panels have a soft gradient and bright corner brackets, and screen titles have a shadow and faint glow.
- **Docking looks the part.** The approach and docking zones are glowing rings with slowly turning dashes, green when you can dock, yellow when you are too fast and red when you are too far. While docking runs, a tractor beam with moving pulses of light pulls the ship in (the other way when undocking) and an arc around the station fills as it completes.

## Beta 16

### Fixed
- **Dying could permanently block the story.** Respawning cleared every active mission, including story missions, without telling the story system. The contact then never offered that mission again and its report option never appeared. Active story missions now survive a respawn (credits, upgrades, cargo and ordinary missions are still reset), and loading a save already stuck this way repairs it.

### Changed
- **Visual polish.** Planets are shaded spheres with a soft atmosphere glow. Each of the five station types has its own silhouette (a wheel hub for Trading Posts, an armoured fortress for Military Bases, a drill-armed core for Mining Stations, a ringed sphere with a dish for Research Stations, a gantry for Shipyards), with halos and blinking lights. Ships have a flickering engine flame with a glow, hull shading and a short exhaust trail. Bandits and patrols have layered armour plating and engine flames, and a boss has a pulsing red aura. The starfield has three depth layers, tinted stars and a twinkle. Explosions are glowing flashes with a shockwave ring and sparks. Taking a hit shakes the screen briefly and flashes the edges red.
- **A new font.** Every screen now uses Exo 2 (SIL Open Font License, bundled in `assets/fonts` with its license in `assets/licenses`) instead of pygame's built-in font. Sizes are scaled so text takes about the same width as before and panels still fit.

### Added
- **Objective pointer.** A small gold arrow circles your ship and points toward the current mission objective, with its name and distance. Story missions are pointed at first. It disappears when you are within about 450 units of the target.
- **Objectives on the large map.** Mission destinations are circled on the map, and ones beyond the edge get an arrow with their name and distance.

## Beta 15

### Added
- **Your own outpost.** After you break the warband on the new frontier in Act 3, Hale offers you the station it held. Claim it and it earns 25 credits a minute while you play, up to 4,000, paid out whenever you dock there. The Logbook's Story page shows where it is and what is waiting. There is a new "Home Port" achievement (19 in all).

### Fixed
- **Starting a new game did not restart the play clock.** Play time (used for market events and the run summary) carried over from the previous game.
- **Achievements unlocked in bulk were partly hidden.** Loading an old save with many qualifying achievements pushed more messages than the notification stack holds. Three or more at once now show as one summary.
- **Saves from betas 9 to 12 could not continue into the new campaign.** If you had already seen Hale's old closing conversation, nothing started Act 1. Loading such a save now moves it into Act 1 and places the new contacts. Hale also tells you where to find them if you ask.
- **macOS downloads were not launchable.** The macOS zip unpacked to a bare `Contents` folder rather than `Space Trader.app`, and the other platforms' zips spilled loose files. Release archives now unpack to a single `Space Trader.app` or `Space Trader` folder. Builds from betas 9 to 13 still have the old layout.
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
