# API Contract

Документ описывает HTTP API между **frontend** и **backend**. Этот контракт стабилен: AI-логика внутри backend может меняться (mock → YOLO → очереди), но формат запросов и ответов остаётся фиксированным.

База URL (dev): `http://localhost:8000`

Префикс API: `/api/v1`

Формат: `application/json`, кодировка UTF-8.

---

## Endpoints overview

| Method | Path | Назначение |
|---|---|---|
| GET | `/api/v1/health` | Проверка живости сервиса |
| POST | `/api/v1/analyze` | Запуск анализа по demo-сценарию |
| GET | `/api/v1/protocols` | Список всех протоколов |
| GET | `/api/v1/protocols/{id}` | Один протокол по id |

Swagger UI: `http://localhost:8000/docs`

---

## Common enums

### `risk_level` / `overall_risk`

| Значение | Цвет в UI | Описание |
|---|---|---|
| `low` | green | угрозы жизни нет |
| `medium` | yellow | требуется наблюдение |
| `high` | orange | требуется срочная помощь |
| `critical` | red | угроза жизни |

### `status`

| Значение | Описание |
|---|---|
| `OK` | состояние стабильное |
| `Minor` | лёгкие повреждения |
| `Serious` | серьёзное состояние |
| `Critical` | критическое состояние |

### `scenario`

`single_unconscious`, `multiple_victims`, `severe_bleeding`, `low_confidence`.

### `priority`

Целое число от `1` (наивысший) до `4` (наименьший).

### `severity_score`

Число с плавающей точкой `[0.0, 1.0]`.

---

## 1. GET /api/v1/health

Простой healthcheck.

**Response 200**

```json
{
  "status": "ok",
  "service": "rescue-vision-ai",
  "version": "0.1.0"
}
```

---

## 2. POST /api/v1/analyze

Главный endpoint. Принимает контекст инцидента и demo-сценарий, возвращает структурированный результат анализа.

### Request body

| Field | Type | Required | Description |
|---|---|---|---|
| `incident_id` | string | yes | ID инцидента |
| `rescuer_id` | string | yes | ID спасателя |
| `scenario` | enum scenario | yes | demo-сценарий |
| `gps` | object | no | координаты спасателя |
| `gps.lat` | number | no | широта |
| `gps.lon` | number | no | долгота |
| `timestamp` | string (ISO 8601) | no | момент съёмки |

Пример:

```json
{
  "incident_id": "inc-001",
  "rescuer_id": "resc-42",
  "scenario": "single_unconscious",
  "gps": { "lat": 55.7558, "lon": 37.6173 },
  "timestamp": "2026-05-14T12:34:56Z"
}
```

### Response 200

| Field | Type | Description |
|---|---|---|
| `analysis_id` | string | Уникальный ID анализа |
| `overall_risk` | enum risk_level | Общий риск по сцене |
| `confidence` | number `[0,1]` | Уверенность AI |
| `scene` | object | Признаки сцены |
| `scene.people_count` | int | Кол-во обнаруженных людей |
| `scene.observations` | string[] | Наблюдения (поза, кровь, дым...) |
| `victims` | Victim[] | Список пострадавших, отсортированный по priority |
| `recommended_actions` | Action[] | Глобальные действия (чеклист) |
| `protocols` | string[] | ID применимых протоколов |
| `quality` | object | Качество входных данных |
| `quality.low_confidence` | bool | Низкая уверенность |
| `quality.notes` | string[] | Заметки о качестве |
| `disclaimer` | string | Юридическая/безопасная формулировка |

#### Victim

| Field | Type | Description |
|---|---|---|
| `id` | int | Локальный id пострадавшего |
| `priority` | int (1–4) | Приоритет спасения |
| `severity_score` | number `[0,1]` | Числовая оценка тяжести |
| `severity_label` | enum risk_level | Текстовая оценка |
| `status` | enum status | OK / Minor / Serious / Critical |
| `bbox` | int[4] \| null | `[x1,y1,x2,y2]`, может быть null на mock |
| `signals` | string[] | Признаки: `no_movement`, `bleeding`, ... |
| `first_aid` | string[] | Конкретные шаги помощи именно для этого пострадавшего |
| `protocols` | string[] | ID применимых протоколов |

#### Action

| Field | Type | Description |
|---|---|---|
| `id` | string | ID действия |
| `title` | string | Короткое название |
| `description` | string | Подробное описание |
| `priority` | int | Порядок в чеклисте |
| `critical` | bool | Подсвечивать красным |

### Пример ответа

```json
{
  "analysis_id": "an-7f3c",
  "overall_risk": "critical",
  "confidence": 0.82,
  "scene": {
    "people_count": 1,
    "observations": [
      "Пострадавший лежит без движения",
      "Видимых преград на сцене нет"
    ]
  },
  "victims": [
    {
      "id": 1,
      "priority": 1,
      "severity_score": 0.88,
      "severity_label": "critical",
      "status": "Critical",
      "bbox": [120, 80, 410, 360],
      "signals": ["lying", "no_movement", "possible_unconscious"],
      "first_aid": [
        "Проверьте безопасность места",
        "Оцените сознание и дыхание",
        "При отсутствии дыхания — начните СЛР по протоколу"
      ],
      "protocols": ["scene_safety", "primary_assessment", "basic_life_support"]
    }
  ],
  "recommended_actions": [
    {
      "id": "ensure_safety",
      "title": "Убедитесь в безопасности места",
      "description": "Оцените сцену на наличие опасностей перед подходом.",
      "priority": 1,
      "critical": true
    },
    {
      "id": "primary_assessment",
      "title": "Первичная оценка состояния",
      "description": "Проверьте сознание, дыхание, кровотечение.",
      "priority": 2,
      "critical": true
    }
  ],
  "protocols": ["scene_safety", "primary_assessment", "basic_life_support"],
  "quality": {
    "low_confidence": false,
    "notes": []
  },
  "disclaimer": "Система носит вспомогательный характер и не заменяет решение спасателя."
}
```

### Поведение по сценариям

| scenario | overall_risk | victims | особенности |
|---|---|---|---|
| `single_unconscious` | `critical` | 1 шт., Critical | подсветить СЛР |
| `multiple_victims` | `high` | 3–5 шт., разной тяжести | включить mass casualty triage |
| `severe_bleeding` | `critical` | 1 шт., Critical | приоритет — остановка кровотечения |
| `low_confidence` | `medium` | 0–1 шт. | `quality.low_confidence = true`, предупреждение |

Подробные правила — в [`docs/ai-triage-rules.md`](ai-triage-rules.md).

---

## 3. GET /api/v1/protocols

Возвращает список всех протоколов.

**Response 200**

```json
{
  "protocols": [
    {
      "id": "scene_safety",
      "title": "Обеспечение безопасности места",
      "tags": ["safety", "primary"]
    },
    {
      "id": "primary_assessment",
      "title": "Первичная оценка пострадавшего",
      "tags": ["primary"]
    }
  ]
}
```

---

## 4. GET /api/v1/protocols/{id}

Возвращает один протокол по id.

**Response 200**

```json
{
  "id": "basic_life_support",
  "title": "Базовая реанимация (BLS)",
  "tags": ["bls", "critical"],
  "steps": [
    "Проверьте безопасность места",
    "Оцените сознание (окликните, аккуратно потрясите за плечо)",
    "Откройте дыхательные пути",
    "Проверьте дыхание в течение 10 секунд",
    "При отсутствии дыхания — начните компрессии 30:2"
  ],
  "disclaimer": "Действуйте согласно официальным протоколам вашей службы."
}
```

**Response 404** — если протокол не найден:

```json
{ "detail": "Protocol not found" }
```

---

## Error format

Все ошибки возвращаются в формате FastAPI:

```json
{
  "detail": "human-readable message"
}
```

Коды:

| Код | Когда |
|---|---|
| 400 | Невалидный JSON / сценарий |
| 404 | Ресурс не найден |
| 422 | Ошибка валидации Pydantic |
| 500 | Внутренняя ошибка |

---

## Версионирование

Все endpoints живут под `/api/v1`. При несовместимых изменениях вводится `/api/v2`, `v1` остаётся стабильным до конца demo.
