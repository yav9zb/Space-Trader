# Changelog

## Beta 1 (unreleased)

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
