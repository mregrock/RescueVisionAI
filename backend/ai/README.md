# backend/ai — AI / Triage / Protocols module

Модуль анализа сцены ЧС. Поддерживает два режима:

- **Mock-режим** — детерминированный анализ по demo-сценарию (для тестов и demo).
- **Real-режим** — анализ реального кадра через две CV-модели.

---

## Структура модуля

```
backend/ai/
├── __init__.py          # analyze() и analyze_image() — точки входа
├── types.py             # enums, веса сигналов, dataclass-структуры
├── scenarios.py         # blueprints для 4 demo-сценариев
├── detector.py          # detect() и detect_from_image()
├── frame_filter.py      # Model 1: YOLOv8n — фильтр кадров без людей
├── triage_model.py      # Model 2: YOLOv8n-pose — детекция + ключевые точки
├── signal_extractor.py  # keypoints + HSV → signals
├── classifier.py        # signals → severity_score / severity_label
├── ranker.py            # сортировка, priority, status, overall_risk
├── advisor.py           # rule-based recommended_actions + first_aid
└── tests/
    └── test_smoke.py    # smoke-тесты на все demo-сценарии
```

---

## Pipeline

### Mock-режим (`analyze(scenario)`)

```
scenario
   │
   ▼ detector.detect()
RawScene, [RawVictim]   ← из заранее заданных blueprints
   │
   ▼ classifier → ranker → advisor
   │
   ▼ dict по API-контракту
```

### Real-режим (`analyze_image(image_bytes)`)

```
image bytes
   │
   ▼ [Model 1] frame_filter.filter_frame()  — YOLOv8n
       нет людей → пустая сцена (Model 2 не запускается)
       есть люди ↓
   ▼ [Model 2] triage_model.analyze()  — YOLOv8n-pose
       bounding boxes + 17 COCO keypoints
   │
   ▼ signal_extractor.extract_signals()
       поза:  lying / sitting / standing
       риски: possible_unconscious, bleeding_visible, severe_bleeding, burns_visible
   │
   ▼ RawScene, [RawVictim]   ← тот же формат, что и mock
   │
   ▼ classifier → ranker → advisor
   │
   ▼ dict по API-контракту
```

---

## Использование

```python
# Mock
from backend.ai import analyze
result = analyze("single_unconscious")

# Real
from backend.ai import analyze_image
with open("photo.jpg", "rb") as f:
    result = analyze_image(f.read(), incident_id="inc-001", rescuer_id="resc-42")
```

---

## Сигналы

| Сигнал | Источник | Метод |
|---|---|---|
| `lying` | bbox aspect ratio / keypoints | геометрия |
| `sitting` | keypoints торса и лодыжек | геометрия |
| `standing` | по умолчанию | геометрия |
| `possible_unconscious` | lying + низкая уверенность keypoints | эвристика |
| `bleeding_visible` | красные пиксели в ROI > 5% | HSV-маска |
| `severe_bleeding` | красные пиксели в ROI > 15% | HSV-маска |
| `burns_visible` | тёмно-коричневые пиксели > 8% | HSV-маска |

`no_movement` из одного кадра не определяется — не выставляется.

---

## Тесты

```bash
pytest backend/ai/tests/test_smoke.py -v
```

Smoke-тесты покрывают mock-режим (все 4 сценария). Real-режим тестируется вручную через `POST /api/v1/analyze/image`.
