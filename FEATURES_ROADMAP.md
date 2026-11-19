# Features Roadmap

This document tracks what's actually implemented versus genuinely still planned. For the full current feature list, see [README.md](README.md).

> This file previously described afterburners, WASD controls, difficulty levels, and enhanced debris physics as upcoming "next release" work. All of that has since shipped (afterburner and WASD controls were already built when this doc was last accurate; difficulty levels, audio, and a full visual overhaul were completed in the beta prep pass). Rewritten to reflect current status rather than carry that stale plan forward.

## Recently Completed (Beta Prep)

- **Difficulty Levels** - 5 levels (Peaceful → Extreme), affecting hazard frequency, enemy spawns, damage, mission rewards/time limits, repair/upgrade costs, and permadeath on Extreme. See `src/difficulty/difficulty_manager.py`.
- **Audio System** - sound effects for weapons/explosions/docking/engines/UI, music stingers, working volume controls. See `src/audio/sound_manager.py`.
- **First-time onboarding hints** - contextual, dismissible, shown once ever.
- **App icon** - packaged build icon and in-game window icon.
- **Full visual redesign** - ship, bandit ships, weapon projectiles, explosions, stations (all 5 types now visually distinct - previously a rendering bug made every station look like a plain circle), planets (gas giants now have properly circle-clipped bands, a signature storm, and optional rings), HUD panel styling, and every menu screen (main menu, trading, mission board, upgrades, save/load, settings) now sharing a consistent starfield-background, accent-bordered look.
- **Packaging** - PyInstaller build producing a standalone app (verified on macOS), a GitHub Actions workflow for cross-platform builds, and correct settings/save/log file locations for a packaged build.
- **Steam integration scaffolding** - see `STEAM_RELEASE_CHECKLIST.md` for what's prepared versus what requires the developer's own Steamworks account.
- **Numerous bug fixes** found by actually rendering and testing rather than just reading code, including a severe frame-rate bug (debris collision sparks accumulating unbounded, ~4.5x slowdown), several screens' content overflowing into fixed-position footers, a critical flight-rendering bug (everything but the starfield could vanish when no station was on screen), and multiple UI strings using Unicode glyphs pygame's default font can't render.
- **Display settings submenu** - the "Display" category was a placeholder that did nothing when selected; now supports Resolution, Display Mode (Windowed/Fullscreen/Borderless), and HUD Scale (0.75x-1.75x, addresses beta feedback about small flight-HUD text). See `SETTINGS.md`.
- **Reputation system** - `min_reputation` mission requirements and `reputation_bonus`/`reputation_loss` reward/penalty fields existed but were never applied; the player's reputation is now tracked, persisted, and shown in the Ship Status HUD and Mission Board.

- **Story foundations** - saved campaign state, event tracking, a dialogue engine and conversation screen, named station contacts (Talk key when docked), and a Logbook (pause menu). Mission save/load was also fixed so in-progress missions keep working after loading.
- **Story prologue** - a three-mission opening chapter driven by authored mission data, conversation choices, and automatic scenes; story missions save and load like any other mission.
- **Escort and bounty missions** - escorts spawn a trader plus an ambush and bandits will attack the escorted trader; bounties spawn a named, labeled pirate captain. Both recover if loaded mid-mission.
- **Patrols, backup, and hostile standing** - Guild patrols hunt bandits; Captains can call backup (H); at -60 standing a faction's patrols attack you and Guild/Pirate stations refuse docking, with ways back (bandit kills in its space, slow cooling off).
- **Smuggling and market events** - contraband inspections at Guild stations, a pirate-market premium, Smuggling Run missions, and timed regional raids/shortages/embargoes shown as market news. Markets now actually refresh over time.
- **Shifting borders and Liberation missions** - region control can change permanently (persisted); destroying a pirate stronghold frees its region. Player outposts are deferred until base building is integrated and saved.
- **Left-handed controls fix** - the default scheme shared keys between dock/trading and undock/upgrades, so a docked player could not undock; station services moved to Z/X/C/V.

## Planned / Not Yet Implemented

### Near-term
- **Auto-Dock / Docking Assist** - manual docking is fully implemented; automated docking and configurable docking sensitivity are not.
- **Steam Achievements / Cloud Saves** - optional Steamworks features, not implemented; would map onto the existing mission-completion events and save system respectively.

### Longer-term / Concept
- **Advanced AI** - formation flying, tactical retreat, adaptive behavior, faction-aware coordination.
- **Faction System** - reputation and relationships with trading guilds, military, pirates, corporations; faction-exclusive missions and territory control.
- **Story Mode** - a narrative campaign with scripted events, distinct from the current sandbox gameplay loop.
- **Multiplayer** - cooperative and competitive modes, a shared universe, guilds. This would be a substantial architectural change (the game is currently single-player/local-state only) and isn't scoped in any detail yet.
- **Visual Effects** - particle systems for explosions/thrust beyond the current layered-polygon effects, environmental effects (nebulae, dust clouds).

## Development Process

- Small, focused commits with a clear "why" in the message - not just "what changed."
- Every rendering change gets verified with an actual rendered screenshot before being called done, not just code review - this is how most of the bugs listed above were actually found.
- `pytest` suite (`tests/`) must stay green; run it after every change, not just at the end.
