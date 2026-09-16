# Steam Release Checklist

What's been prepared in the codebase, and what only you can do (account
creation, payment, legal/tax forms, and store submission are things an
AI assistant can't and shouldn't do on your behalf).

> **Sequencing:** the plan is a GitHub beta first, Steam after - see
> [GITHUB_RELEASE_CHECKLIST.md](GITHUB_RELEASE_CHECKLIST.md) for that
> nearer-term step. Nothing here blocks the GitHub beta; this document
> only matters once you're ready to move toward Steam.

## Done in the codebase

- **Packaged build**: `spacetrader.spec` produces a standalone build via
  PyInstaller (`./venv/bin/pyinstaller spacetrader.spec`). Verified
  locally on macOS - produces `dist/Space Trader.app`, launches clean,
  and correctly writes settings/saves/logs to
  `~/Library/Application Support/SpaceTrader/` rather than inside the
  (read-only, once signed) bundle. Windows/Linux builds will need to
  happen on those platforms - see `.github/workflows/build.yml` below.
- **CI build workflow**: `.github/workflows/build.yml` runs the test
  suite and, on a version tag push, builds all three platforms
  (macOS/Windows/Linux) via a GitHub Actions matrix and uploads each as
  a build artifact. The repo now has a GitHub remote
  ([yav9zb/Space-Trader](https://github.com/yav9zb/Space-Trader)) but
  this workflow still hasn't been validated against a real CI run -
  push a tag and check the Actions tab.
- **Steamworks scaffolding**: `src/steam/steam_manager.py` looks for a
  native Steamworks library (`steam_api64.dll` / `libsteam_api.dylib` /
  `libsteam_api.so`) next to the executable and calls
  `SteamAPI_InitFlat()`/`SteamAPI_Shutdown()` if found. **This has not
  been tested against a real Steamworks SDK** - I don't have access to
  one (it requires your Steamworks partner account to download) and
  Valve has changed this exact API before without a changelog note
  (SDK 1.59, Feb 2024). Read the caveats in that file's docstring and
  verify the function signature against whatever SDK version you
  actually download before relying on it. Until the real SDK/DLL is
  present, this is a total no-op and the game runs exactly as it does
  today - that's by design, so standalone/itch.io builds keep working
  regardless of Steam.
- **All-rights-reserved licensing**: dropped the earlier unbacked MIT
  claim (see the repo hygiene commit) since MIT doesn't make sense for
  a paid release.

## Only you can do these

1. **Create a Steamworks partner account** at
   [partner.steamgames.com](https://partner.steamgames.com) and pay the
   $100 Steam Direct fee. (I can't create accounts or make payments on
   your behalf.)
2. **Complete tax/identity/banking forms** in the partner dashboard -
   required before Steam will pay out revenue.
3. **Register the app** to get a real AppID, then:
   - Download the actual Steamworks SDK from the partner site.
   - Verify/fix `src/steam/steam_manager.py` against the real SDK
     headers (see the caveats above).
   - Create a `steam_appid.txt` next to the executable during
     development containing your AppID (Valve's standard dev-testing
     mechanism), and place the real `steam_api64.dll` /
     `libsteam_api.dylib` / `libsteam_api.so` next to the built
     executable (update `spacetrader.spec`'s `datas`/`binaries` to
     bundle it).
4. **Store page assets**: capsule images (header, small, main, vertical
   - exact sizes are in Steamworks documentation), at least 5
     screenshots, and ideally a trailer. I can capture in-game
     screenshots and draft store page copy on request, but key art and
     video editing are a design/production task best done by you or a
     hired artist.
5. **Fill out the store page** itself (description, tags, pricing,
   age rating questionnaire) in the partner dashboard.
6. **Upload the build via SteamPipe** (Valve's `steamcmd`-based upload
   tool - the partner site has a walkthrough once your AppID exists)
   and submit for review.
7. **Optional but common for Steam titles**: Steam Cloud (map to the
   existing save system in `src/save_system.py`) and Achievements (map
   to mission-completion/milestone events - needs achievement
   definitions configured in the partner dashboard first). Neither is
   implemented yet; flag if you want these before launch.

## Suggested order

Steps 1-3 first (there's a review/verification lag on Valve's side
after account creation), then packaging polish and store assets in
parallel, then upload and submit once both are ready.
