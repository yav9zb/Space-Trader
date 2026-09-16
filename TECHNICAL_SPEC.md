# Technical Specification: Next Release Features (Superseded)

This document originally specified four features as upcoming work: Afterburners, WASD Controls, Difficulty Levels, and Enhanced Debris Physics. **All four have since shipped.** Two (afterburner, WASD controls) were already implemented - inline in `src/entities/ship.py` and `src/input/control_schemes.py` respectively, not as the separate modules this document originally specced - by the time this was reviewed for the beta. The other two (Difficulty Levels, Enhanced Debris Physics) were built during beta prep, also not always matching this document's original class designs exactly (implementation details evolved during actual development, as they do).

Keeping this file for history rather than deleting it, but its code samples and "planned" framing are no longer accurate - don't treat them as current design docs.

For what's actually implemented today, see [README.md](README.md). For what's still genuinely planned, see [FEATURES_ROADMAP.md](FEATURES_ROADMAP.md).

Where to find the real implementations:
- **Afterburner**: `src/entities/ship.py` (fields prefixed `afterburner_*`, plus `get_afterburner_status()`)
- **Control schemes**: `src/input/control_schemes.py` (`ControlScheme.RIGHT_HANDED`/`LEFT_HANDED`)
- **Difficulty Levels**: `src/difficulty/difficulty_manager.py`
- **Debris physics**: `src/entities/debris.py` and `src/systems/debris_field_manager.py`
