# GitHub Beta Release Checklist

The near-term goal: a public beta release on GitHub, before pursuing Steam
(see [STEAM_RELEASE_CHECKLIST.md](STEAM_RELEASE_CHECKLIST.md) for that
later step). This is much lower-friction than Steam - no account/fee/review
process, just a tagged release with downloadable builds.

## Already true

- **Repo is public**: [github.com/yav9zb/Space-Trader](https://github.com/yav9zb/Space-Trader).
- **Docs are current**: README, CHANGELOG, and the system docs have been
  reviewed against the actual implementation as of this beta (see the
  "Docs update for beta release" work - stale key bindings, broken file
  references, and an outdated roadmap were all fixed).
- **`.github/workflows/build.yml`** builds all three platforms on a
  version tag push (`v*`) and runs the test suite on every push.

## Steps (roughly in order)

1. **Push everything** to `origin/main` if you haven't already
   (`git push origin main`).
2. **Tag a version** to trigger the build workflow, e.g.:
   ```bash
   git tag v0.1.0-beta.1
   git push origin v0.1.0-beta.1
   ```
   This is the first real run of `.github/workflows/build.yml` - it
   hasn't been validated against actual GitHub Actions yet, so expect to
   possibly debug it. Check the Actions tab after pushing the tag.
3. **Verify the build artifacts** the workflow produces (downloadable
   from the Actions run) actually launch on each platform before
   attaching them anywhere public. The macOS build has been verified
   locally in this session; Windows and Linux have not been tested at
   all.
4. **Create the GitHub Release**:
   - Go to the repo's Releases page → "Draft a new release" → pick the
     tag you just pushed.
   - Check **"Set as a pre-release"** - this is a beta, not a stable
     release; GitHub's UI and RSS/notification behavior treat
     pre-releases differently, and it sets the right expectation for
     anyone who finds it.
   - Attach the build artifacts from step 3 (download them from the
     Actions run and upload as release assets - the workflow doesn't
     currently attach them automatically; that's a reasonable follow-up
     if you end up doing this repeatedly).
   - Use [CHANGELOG.md](CHANGELOG.md)'s "Beta 1" section as a starting
     point for release notes, trimmed/rewritten in your own voice.
5. **Announce/share** wherever you're planning to find beta testers.
   Point them at the Issues tab for bug reports (the README's "Known
   Issues" section already invites this).

## Things worth deciding before or during this

- **Repo description/topics** on GitHub (currently unset, worth adding
  for discoverability if you want randos finding it).
- Whether to keep iterating with more beta tags (`v0.1.0-beta.2`, etc.)
  as issues come in, or hold at one build until you're ready for a wider
  push.
