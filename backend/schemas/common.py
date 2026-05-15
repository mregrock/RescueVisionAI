from enum import Enum


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class VictimStatus(str, Enum):
    ok = "OK"
    minor = "Minor"
    serious = "Serious"
    critical = "Critical"


class Scenario(str, Enum):
    single_unconscious = "single_unconscious"
    multiple_victims = "multiple_victims"
    severe_bleeding = "severe_bleeding"
    low_confidence = "low_confidence"
