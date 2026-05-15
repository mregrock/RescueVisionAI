"""Типы и веса сигналов AI-модуля. Правила: docs/ai-triage-rules.md."""

from dataclasses import dataclass, field

from ..schemas.common import Scenario

SCENARIO_SINGLE_UNCONSCIOUS = Scenario.single_unconscious.value
SCENARIO_MULTIPLE_VICTIMS = Scenario.multiple_victims.value
SCENARIO_SEVERE_BLEEDING = Scenario.severe_bleeding.value
SCENARIO_LOW_CONFIDENCE = Scenario.low_confidence.value

SUPPORTED_SCENARIOS = tuple(s.value for s in Scenario)

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"

STATUS_OK = "OK"
STATUS_MINOR = "Minor"
STATUS_SERIOUS = "Serious"
STATUS_CRITICAL = "Critical"

SIGNAL_LYING = "lying"
SIGNAL_SITTING = "sitting"
SIGNAL_STANDING = "standing"
SIGNAL_NO_MOVEMENT = "no_movement"
SIGNAL_WEAK_MOVEMENT = "weak_movement"
SIGNAL_BLEEDING_VISIBLE = "bleeding_visible"
SIGNAL_SEVERE_BLEEDING = "severe_bleeding"
SIGNAL_BURNS_VISIBLE = "burns_visible"
SIGNAL_POSSIBLE_FRACTURE = "possible_fracture"
SIGNAL_POSSIBLE_UNCONSCIOUS = "possible_unconscious"

SCENE_SIGNAL_MULTIPLE_VICTIMS = "multiple_victims"
SCENE_SIGNAL_SMOKE_OR_FIRE = "smoke_or_fire"
SCENE_SIGNAL_LOW_VISIBILITY = "low_visibility"

# Аддитивные веса сигналов пострадавшего; сумма клампится в [0, 1].
VICTIM_SIGNAL_WEIGHTS: dict[str, float] = {
    SIGNAL_LYING: 0.20,
    SIGNAL_SITTING: 0.05,
    SIGNAL_STANDING: 0.00,
    SIGNAL_NO_MOVEMENT: 0.35,
    SIGNAL_WEAK_MOVEMENT: 0.15,
    SIGNAL_BLEEDING_VISIBLE: 0.30,
    SIGNAL_SEVERE_BLEEDING: 0.45,
    SIGNAL_BURNS_VISIBLE: 0.25,
    SIGNAL_POSSIBLE_FRACTURE: 0.15,
    SIGNAL_POSSIBLE_UNCONSCIOUS: 0.30,
}

# Контекст сцены, добавляемый каждому пострадавшему.
SCENE_SIGNAL_WEIGHTS: dict[str, float] = {
    SCENE_SIGNAL_MULTIPLE_VICTIMS: 0.10,
    SCENE_SIGNAL_SMOKE_OR_FIRE: 0.15,
    SCENE_SIGNAL_LOW_VISIBILITY: 0.00,
}

# При равном score эти сигналы поднимают пострадавшего выше в приоритете.
TIEBREAKER_SIGNALS = (
    SIGNAL_SEVERE_BLEEDING,
    SIGNAL_POSSIBLE_UNCONSCIOUS,
)


@dataclass
class RawVictim:
    local_id: int
    signals: list[str] = field(default_factory=list)
    bbox: list[int] | None = None


@dataclass
class RawScene:
    people_count: int
    observations: list[str] = field(default_factory=list)
    scene_signals: list[str] = field(default_factory=list)
    base_confidence: float = 0.85


@dataclass
class ClassifiedVictim:
    local_id: int
    signals: list[str]
    bbox: list[int] | None
    severity_score: float
    severity_label: str


@dataclass
class RankedVictim:
    id: int
    priority: int
    severity_score: float
    severity_label: str
    status: str
    bbox: list[int] | None
    signals: list[str]
