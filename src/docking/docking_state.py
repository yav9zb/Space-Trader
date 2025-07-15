from enum import Enum


class DockingState(Enum):
    """Enumeration of possible docking states for ships."""
    FREE_FLIGHT = "free_flight"
    APPROACHING = "approaching"
    DOCKING = "docking"
    DOCKED = "docked"
    UNDOCKING = "undocking"


class DockingResult(Enum):
    """Results of docking attempts."""
    SUCCESS = "success"
    TOO_FAST = "too_fast"
    TOO_FAR = "too_far"
    NO_TARGET = "no_target"
    ALREADY_DOCKED = "already_docked"
    INVALID_STATE = "invalid_state"