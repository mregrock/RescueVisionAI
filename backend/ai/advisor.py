"""Rule-based рекомендации и first-aid. Правила: docs/ai-triage-rules.md."""

from .types import (
    RankedVictim,
    RawScene,
    SCENE_SIGNAL_LOW_VISIBILITY,
    SIGNAL_BLEEDING_VISIBLE,
    SIGNAL_BURNS_VISIBLE,
    SIGNAL_LYING,
    SIGNAL_NO_MOVEMENT,
    SIGNAL_POSSIBLE_FRACTURE,
    SIGNAL_POSSIBLE_UNCONSCIOUS,
    SIGNAL_SEVERE_BLEEDING,
)


_ACTIONS: dict[str, dict] = {
    "ensure_safety": {
        "title": "Убедитесь в безопасности места",
        "description": (
            "Оцените сцену на наличие опасностей (огонь, дым, обрушения, "
            "электричество, транспорт) перед подходом к пострадавшим."
        ),
        "critical": True,
        "protocols": ["scene_safety"],
    },
    "primary_assessment": {
        "title": "Проведите первичную оценку",
        "description": (
            "Быстро оцените сознание, дыхание и наличие сильного "
            "кровотечения у каждого пострадавшего согласно протоколу."
        ),
        "critical": True,
        "protocols": ["primary_assessment"],
    },
    "check_consciousness_breathing": {
        "title": "Проверьте сознание и дыхание",
        "description": (
            "Окликните пострадавшего, проверьте реакцию. В течение не "
            "более 10 секунд оцените наличие нормального дыхания."
        ),
        "critical": True,
        "protocols": ["primary_assessment"],
    },
    "start_bls": {
        "title": "Возможна критическая ситуация — будьте готовы к СЛР",
        "description": (
            "При отсутствии нормального дыхания начните базовую "
            "реанимацию (BLS) согласно протоколу и регламенту вашей службы."
        ),
        "critical": True,
        "protocols": ["basic_life_support"],
    },
    "stop_bleeding": {
        "title": "Контролируйте кровотечение",
        "description": (
            "При видимом сильном кровотечении прижмите рану, наложите "
            "давящую повязку, при необходимости — жгут выше раны согласно протоколу."
        ),
        "critical": True,
        "protocols": ["severe_bleeding"],
    },
    "mass_triage": {
        "title": "Проведите массовую сортировку",
        "description": (
            "Пострадавших несколько — действуйте по протоколу массовой "
            "сортировки. Помощь в первую очередь — тем, у кого есть угроза жизни."
        ),
        "critical": True,
        "protocols": ["mass_casualty_triage"],
    },
    "low_confidence_warning": {
        "title": "Оценка ненадёжна — требуется визуальный осмотр",
        "description": (
            "Качество изображения низкое (дым/темнота). Не полагайтесь "
            "только на оценку системы, обязательно проведите визуальный осмотр."
        ),
        "critical": False,
        "protocols": [],
    },
}

# Стабильный порядок чеклиста; реальный список фильтруется по триггерам.
_ACTION_ORDER = [
    "ensure_safety",
    "primary_assessment",
    "check_consciousness_breathing",
    "start_bls",
    "stop_bleeding",
    "mass_triage",
    "low_confidence_warning",
]


def _has_any_signal(victims: list[RankedVictim], *signals: str) -> bool:
    target = set(signals)
    return any(target.intersection(v.signals) for v in victims)


def build_recommended_actions(
    scene: RawScene,
    victims: list[RankedVictim],
    low_confidence: bool,
) -> list[dict]:
    active: list[str] = ["ensure_safety", "primary_assessment"]

    if _has_any_signal(victims, SIGNAL_LYING, SIGNAL_NO_MOVEMENT):
        active.append("check_consciousness_breathing")
    if _has_any_signal(victims, SIGNAL_POSSIBLE_UNCONSCIOUS):
        active.append("start_bls")
    if _has_any_signal(victims, SIGNAL_BLEEDING_VISIBLE, SIGNAL_SEVERE_BLEEDING):
        active.append("stop_bleeding")
    if scene.people_count >= 2:
        active.append("mass_triage")
    if low_confidence or SCENE_SIGNAL_LOW_VISIBILITY in scene.scene_signals:
        active.append("low_confidence_warning")

    ordered = [a for a in _ACTION_ORDER if a in active]
    return [
        {
            "id": action_id,
            "title": _ACTIONS[action_id]["title"],
            "description": _ACTIONS[action_id]["description"],
            "priority": idx + 1,
            "critical": _ACTIONS[action_id]["critical"],
        }
        for idx, action_id in enumerate(ordered)
    ]


def used_protocols(
    scene: RawScene,
    victims: list[RankedVictim],
    low_confidence: bool,
) -> list[str]:
    actions = build_recommended_actions(scene, victims, low_confidence)
    seen: list[str] = []
    for action in actions:
        for proto_id in _ACTIONS[action["id"]]["protocols"]:
            if proto_id not in seen:
                seen.append(proto_id)
    return seen


_FIRST_AID_RULES: dict[str, str] = {
    SIGNAL_LYING: "Оцените сознание и дыхание согласно протоколу первичной оценки.",
    SIGNAL_NO_MOVEMENT: "Оцените сознание и дыхание согласно протоколу первичной оценки.",
    SIGNAL_POSSIBLE_UNCONSCIOUS: (
        "При отсутствии нормального дыхания — начните СЛР согласно протоколу BLS."
    ),
    SIGNAL_BLEEDING_VISIBLE: "Прижмите рану и наложите давящую повязку согласно протоколу.",
    SIGNAL_SEVERE_BLEEDING: (
        "Возможно сильное кровотечение — наложите давящую повязку, при "
        "необходимости жгут выше раны согласно протоколу."
    ),
    SIGNAL_BURNS_VISIBLE: (
        "Охладите ожог чистой водой 10–20 минут, накройте чистой повязкой. "
        "Не вскрывайте пузыри."
    ),
    SIGNAL_POSSIBLE_FRACTURE: (
        "Иммобилизуйте конечность, не перемещайте пострадавшего без необходимости."
    ),
}

_SIGNAL_TO_PROTOCOL: dict[str, str] = {
    SIGNAL_LYING: "primary_assessment",
    SIGNAL_NO_MOVEMENT: "primary_assessment",
    SIGNAL_POSSIBLE_UNCONSCIOUS: "basic_life_support",
    SIGNAL_BLEEDING_VISIBLE: "severe_bleeding",
    SIGNAL_SEVERE_BLEEDING: "severe_bleeding",
    SIGNAL_BURNS_VISIBLE: "burns",
    SIGNAL_POSSIBLE_FRACTURE: "fractures",
}

_SAFETY_STEP = "Убедитесь в безопасности места перед оказанием помощи."


def build_first_aid(victim: RankedVictim) -> list[str]:
    steps: list[str] = [_SAFETY_STEP]
    for signal in victim.signals:
        step = _FIRST_AID_RULES.get(signal)
        if step and step not in steps:
            steps.append(step)
    return steps


def build_victim_protocols(victim: RankedVictim) -> list[str]:
    result: list[str] = ["scene_safety"]
    for signal in victim.signals:
        proto = _SIGNAL_TO_PROTOCOL.get(signal)
        if proto and proto not in result:
            result.append(proto)
    return result


DISCLAIMER = (
    "Система носит вспомогательный характер и не заменяет решение "
    "спасателя. Действуйте согласно регламентам вашей службы."
)
