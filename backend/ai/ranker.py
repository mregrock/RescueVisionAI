from .types import (
    ClassifiedVictim,
    RankedVictim,
    RISK_CRITICAL,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    STATUS_CRITICAL,
    STATUS_MINOR,
    STATUS_OK,
    STATUS_SERIOUS,
    TIEBREAKER_SIGNALS,
)

_LABEL_TO_STATUS = {
    RISK_LOW: STATUS_OK,
    RISK_MEDIUM: STATUS_MINOR,
    RISK_HIGH: STATUS_SERIOUS,
    RISK_CRITICAL: STATUS_CRITICAL,
}

_RISK_ORDER = [RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL]


def label_to_status(label: str) -> str:
    return _LABEL_TO_STATUS.get(label, STATUS_OK)


def _tiebreaker_score(victim: ClassifiedVictim) -> int:
    return sum(1 for s in victim.signals if s in TIEBREAKER_SIGNALS)


def rank(victims: list[ClassifiedVictim]) -> list[RankedVictim]:
    # Сортировка: severity DESC -> tiebreaker DESC -> local_id ASC (стабильность).
    sorted_victims = sorted(
        victims,
        key=lambda v: (-v.severity_score, -_tiebreaker_score(v), v.local_id),
    )
    return [
        RankedVictim(
            id=v.local_id,
            priority=i,
            severity_score=v.severity_score,
            severity_label=v.severity_label,
            status=label_to_status(v.severity_label),
            bbox=v.bbox,
            signals=list(v.signals),
        )
        for i, v in enumerate(sorted_victims, start=1)
    ]


def overall_risk(victims: list[RankedVictim]) -> str:
    if not victims:
        return RISK_LOW
    rank_idx = {label: i for i, label in enumerate(_RISK_ORDER)}
    return _RISK_ORDER[max(rank_idx.get(v.severity_label, 0) for v in victims)]
