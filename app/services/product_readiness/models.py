from enum import Enum

from pydantic import BaseModel


class CapabilityPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class CapabilityStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    HARDENED = "hardened"
    PILOT_READY = "pilot_ready"
    PRODUCTION_READY = "production_ready"


class Capability(BaseModel):
    id: str

    name: str

    category: str

    priority: CapabilityPriority

    status: CapabilityStatus

    required_for_mlp: bool = False

    required_for_pilot: bool = False

    security_reviewed: bool = False

    ux_complete: bool = False

    tests_passing: bool = False

    documented: bool = False

    notes: str | None = None