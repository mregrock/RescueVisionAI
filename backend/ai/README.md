# backend/ai — AI / Triage / Protocols module

Mock-реализация AI-логики RescueVisionAI для MVP.

Этот модуль:

- получает имя demo-сценария;
- эмулирует детекцию сцены и пострадавших;
- вычисляет `severity_score`, `severity_label`, `priority`, `status`;
- собирает rule-based рекомендации и шаги первой помощи;
- возвращает структуру в точности по [`docs/api-contract.md`](../../docs/api-contract.md).

В будущем mock-`detector` будет заменён на YOLOv8 + классификатор, **без изменений API и без правок остальных файлов модуля**.

---

## Quick start (для backend-разработчика)

```python
from backend.ai import analyze

result = analyze("single_unconscious")
# result — dict, готовый к сериализации в Pydantic-схему /api/v1/analyze
```

Поддерживаемые сценарии:

```python
from backend.ai.types import SUPPORTED_SCENARIOS
# ("single_unconscious", "multiple_victims", "severe_bleeding", "low_confidence")
```

Неизвестный сценарий → `ValueError`. На уровне FastAPI это удобно конвертировать в HTTP 400/422.

---

## Структура модуля

```
backend/ai/
├── __init__.py        # analyze() — единая точка входа
├── types.py           # enums, веса сигналов, dataclass-структуры
├── scenarios.py       # blueprints для 4 demo-сценариев
├── detector.py        # mock-детектор: scenario -> (scene, victims)
├── classifier.py      # signals -> severity_score / severity_label
├── ranker.py          # сортировка, priority, status, overall_risk
├── advisor.py         # rule-based recommended_actions + first_aid
├── requirements.txt   # заглушка под будущие зависимости
└── tests/
    └── test_smoke.py  # 11 smoke-тестов на все сценарии
```

Pipeline `analyze()`:

```
scenario
   │
   ▼ detector.detect()
RawScene, [RawVictim]
   │
   ▼ classifier.classify()
[ClassifiedVictim]   # + severity_score, severity_label
   │
   ▼ ranker.rank()  +  ranker.overall_risk()
[RankedVictim], overall_risk
   │
   ▼ advisor.build_recommended_actions()
   ▼ advisor.used_protocols()
   ▼ advisor.build_first_aid() / build_victim_protocols() (per victim)
   │
   ▼ __init__.analyze() сериализует всё в dict по API-контракту
```

---

## Что возвращает `analyze()`

См. [`docs/api-contract.md`](../../docs/api-contract.md), раздел **POST /api/v1/analyze → Response 200**.

Поля верхнего уровня:

- `analysis_id` — строка вида `an-xxxxxxxx`
- `overall_risk` — `low` / `medium` / `high` / `critical`
- `confidence` — `[0.0, 1.0]`
- `scene` — `{ people_count, observations }`
- `victims` — список (отсортирован по `priority` 1..N)
- `recommended_actions` — глобальный чеклист действий
- `protocols` — ID применимых протоколов
- `quality` — `{ low_confidence, notes }`
- `disclaimer` — обязательная safety-формулировка
- `scenario` — эхо имени сценария (для удобства)

---

## Поведение по сценариям

| Scenario | overall_risk | people_count | Ключевые actions / protocols |
|---|---|---|---|
| `single_unconscious` | `critical` | 1 | `ensure_safety`, `primary_assessment`, `check_consciousness_breathing`, `start_bls` + `basic_life_support` |
| `severe_bleeding` | `high` / `critical` | 1 | `stop_bleeding` + `severe_bleeding` |
| `multiple_victims` | `high` | 3 | `mass_triage`, `stop_bleeding` + `mass_casualty_triage` |
| `low_confidence` | `medium` | 1 | `low_confidence_warning`, `quality.low_confidence = true` |

Все правила scoring и mapping — в [`docs/ai-triage-rules.md`](../../docs/ai-triage-rules.md).

---

## Тесты

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
python3 -m pytest backend/ai/tests/test_smoke.py -v
```

Покрытие smoke-тестов:

- структура ответа соответствует контракту для всех 4 сценариев;
- `single_unconscious` → `critical` + BLS;
- `severe_bleeding` → `stop_bleeding` + протокол `severe_bleeding`;
- `multiple_victims` → массовая сортировка, priority 1..N без повторов;
- `low_confidence` → `quality.low_confidence == true`;
- неизвестный сценарий → `ValueError`;
- пострадавшие всегда отсортированы по `priority`;
- `disclaimer` присутствует и содержит safety-формулировку.

---

## Интеграция с backend (FastAPI)

Минимальный пример в роуте `/api/v1/analyze`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.ai import analyze
from backend.ai.types import SUPPORTED_SCENARIOS

router = APIRouter(prefix="/api/v1")


class AnalyzeRequest(BaseModel):
    incident_id: str
    rescuer_id: str
    scenario: str
    # gps, timestamp — опционально


@router.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest) -> dict:
    if req.scenario not in SUPPORTED_SCENARIOS:
        raise HTTPException(status_code=400, detail="Unknown scenario")
    return analyze(req.scenario)
```

Pydantic-схему ответа `AnalyzeResponse` backend описывает у себя на основе [`docs/api-contract.md`](../../docs/api-contract.md) — AI-модуль возвращает уже готовый dict совместимого формата.

---

## Safety / disclaimers

Все формулировки модуля проходят правило «не ставить диагноз»:

- никаких «жив/мёртв», «без сознания» (только «возможно без сознания»);
- никаких конкретных препаратов и дозировок;
- везде ссылка на «протоколы вашей службы»;
- обязательный `disclaimer` в ответе.

Полные правила — в разделе **Safety limitations** [`docs/ai-triage-rules.md`](../../docs/ai-triage-rules.md).

---

## Расширение (mock → real AI)

Когда придёт время заменить mock на реальные модели:

1. Поменять `detector.py`:
   - принимать `image: np.ndarray | bytes | path` вместо `scenario`;
   - внутри — YOLOv8 для bounding boxes + лёгкий классификатор сигналов;
   - возвращать те же `RawScene` и `RawVictim`.
2. `classifier.py`, `ranker.py`, `advisor.py` **не трогать**.
3. В `__init__.py` оставить функцию `analyze(...)` — изменится только её сигнатура (вместо строки-сценария пойдёт кадр).

Контракт API при этом останется прежним.
