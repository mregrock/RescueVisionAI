# AI Triage Rules

Документ описывает **логику mock AI-модуля**: какие сигналы он «распознаёт» на сцене, как считает severity, как преобразует score в risk и priority, и как выбирает рекомендации.

Цель — сделать поведение mock-модуля **детерминированным и понятным**, чтобы:

- Frontend получал стабильный результат для demo.
- В будущем mock можно было заменить на реальный YOLO + классификатор без изменения API.
- Все формулировки оставались **безопасными** (без диагнозов).

---

## Supported scenarios

| Scenario | Описание | Ожидаемый overall_risk |
|---|---|---|
| `single_unconscious` | Один лежащий без движения | `critical` |
| `multiple_victims` | Несколько пострадавших разной тяжести | `high` |
| `severe_bleeding` | Видимое сильное кровотечение | `critical` |
| `low_confidence` | Плохое качество кадра (дым/темнота) | `medium` |

---

## Scene signals

Mock-модуль формирует список «наблюдений сцены» из набора заранее заданных сигналов. Каждый сигнал вносит вклад в severity score пострадавшего (или общий risk сцены).

| Signal | Категория | Δ severity_score | Применяется к |
|---|---|---|---|
| `lying` | поза | +0.20 | victim |
| `sitting` | поза | +0.05 | victim |
| `standing` | поза | 0.00 | victim |
| `no_movement` | движение | +0.35 | victim |
| `weak_movement` | движение | +0.15 | victim |
| `bleeding_visible` | травма | +0.30 | victim |
| `severe_bleeding` | травма | +0.45 | victim |
| `burns_visible` | травма | +0.25 | victim |
| `possible_fracture` | травма | +0.15 | victim |
| `possible_unconscious` | сознание | +0.30 | victim |
| `multiple_victims` | сцена | +0.10 ко всем | scene |
| `smoke_or_fire` | опасность | +0.15 ко всем | scene |
| `low_visibility` | качество | — снижает confidence | scene |

Все score обрезаются в диапазон `[0.0, 1.0]`.

---

## Victim scoring

```
severity_score = clamp(
    base_score +
    sum(victim_signal_deltas) +
    sum(scene_modifier_deltas),
    0.0,
    1.0
)
```

- `base_score` = 0.0
- `victim_signal_deltas` — суммируем по сигналам этого пострадавшего.
- `scene_modifier_deltas` — добавки от общесценических сигналов (`smoke_or_fire`, `multiple_victims`).

---

## Risk mapping

`severity_score` → `severity_label` / `overall_risk`:

| Score range | Level |
|---|---|
| `[0.00, 0.25)` | `low` |
| `[0.25, 0.50)` | `medium` |
| `[0.50, 0.80)` | `high` |
| `[0.80, 1.00]` | `critical` |

`overall_risk` сцены = **максимальный** уровень среди всех пострадавших. Если пострадавших нет — `low`.

---

## Status mapping

`severity_label` → `status` для UI:

| severity_label | status |
|---|---|
| `low` | `OK` |
| `medium` | `Minor` |
| `high` | `Serious` |
| `critical` | `Critical` |

---

## Priority mapping

Приоритет — порядковый номер обработки пострадавшего в чеклисте спасателя.

Алгоритм:

1. Сортируем пострадавших по `severity_score` по убыванию.
2. Назначаем `priority = 1, 2, 3, ...` (1 = самый тяжёлый).
3. В случае равных score побеждает тот, у кого есть сигнал `severe_bleeding` или `possible_unconscious`.

Ограничение для MVP: максимум 4 пострадавших, `priority` ∈ {1, 2, 3, 4}.

---

## Confidence

`confidence` ∈ `[0.0, 1.0]` — насколько mock «уверен» в результате.

| Условие | confidence |
|---|---|
| Сценарий `low_confidence` | 0.35 |
| Сценарий `multiple_victims` | 0.70 |
| Прочие сценарии | 0.85 |

Если `confidence < 0.5` → `quality.low_confidence = true` и в `quality.notes` добавляется строка вроде «Плохое качество изображения, требуется визуальный осмотр».

---

## Recommended actions rules (rule-based)

Глобальные рекомендации формируются как **детерминированный чеклист** из набора правил. Порядок важен.

| Правило | Условие включения | Action id |
|---|---|---|
| Безопасность места | всегда | `ensure_safety` |
| Первичная оценка | всегда | `primary_assessment` |
| Проверка сознания и дыхания | есть victim с `lying` или `no_movement` | `check_consciousness_breathing` |
| Базовая реанимация (BLS) | есть victim с `possible_unconscious` | `start_bls` |
| Контроль кровотечения | есть victim с `bleeding_visible` или `severe_bleeding` | `stop_bleeding` |
| Массовая сортировка | `people_count >= 2` | `mass_triage` |
| Предупреждение о низкой уверенности | `low_confidence == true` | `low_confidence_warning` |

Каждое правило ссылается на соответствующий протокол в [`protocols.json`](../protocols.json) — см. таблицу в [`docs/api-contract.md`](api-contract.md).

---

## Per-victim first_aid rules

Список конкретных шагов для одного пострадавшего собирается из его сигналов:

| Сигнал | Добавляет шаг |
|---|---|
| `lying`, `no_movement` | «Оцените сознание и дыхание согласно протоколу» |
| `possible_unconscious` | «При отсутствии дыхания — начните СЛР 30:2» |
| `bleeding_visible` | «Прижмите рану и наложите давящую повязку» |
| `severe_bleeding` | «Возможно сильное кровотечение — используйте жгут выше раны согласно протоколу» |
| `burns_visible` | «Охладите ожог чистой водой, не вскрывайте пузыри» |
| `possible_fracture` | «Иммобилизуйте конечность, не перемещайте без необходимости» |

В начало списка всегда добавляется: **«Убедитесь в безопасности места перед оказанием помощи»**.

---

## Scenario blueprints (детерминированный mock)

Чтобы demo был воспроизводимым, mock возвращает заранее заданные конфигурации:

### `single_unconscious`

- `people_count = 1`
- Victim #1: signals = `["lying", "no_movement", "possible_unconscious"]`
- Ожидаемый score ≈ `0.85` → `critical`
- Активны: `ensure_safety`, `primary_assessment`, `check_consciousness_breathing`, `start_bls`

### `severe_bleeding`

- `people_count = 1`
- Victim #1: signals = `["sitting", "severe_bleeding"]`
- Ожидаемый score ≈ `0.50–0.60` → `high`/`critical`
- Активны: `ensure_safety`, `primary_assessment`, `stop_bleeding`

### `multiple_victims`

- `people_count = 3`
- Victim #1: `["lying", "no_movement"]` → critical
- Victim #2: `["sitting", "bleeding_visible"]` → high
- Victim #3: `["standing", "weak_movement"]` → medium
- Активны: `ensure_safety`, `primary_assessment`, `mass_triage`, `stop_bleeding`

### `low_confidence`

- `people_count = 1` (или 0)
- signals = `["low_visibility"]`
- `confidence = 0.35`, `quality.low_confidence = true`
- Активны: `ensure_safety`, `primary_assessment`, `low_confidence_warning`

---

## Safety limitations

Mock-модуль **не** делает следующего:

- не ставит медицинских диагнозов;
- не называет конкретные препараты и дозировки;
- не утверждает, что пострадавший «жив» или «мёртв»;
- не оценивает уголовно-правовые аспекты.

Все формулировки используют осторожные конструкции:

- «возможна критическая ситуация»;
- «проверьте согласно протоколу»;
- «оценка ненадёжна, требуется визуальный осмотр»;
- «система носит вспомогательный характер и не заменяет решение спасателя».

Эта формулировка обязательна в поле `disclaimer` каждого ответа `/analyze`.

---

## Migration path: mock → real AI

Когда mock будет заменяться на реальную модель:

1. `detector` — YOLOv8 возвращает bounding boxes и `people_count`.
2. `classifier` — отдельная модель / эвристика по позе и видимым повреждениям выставляет сигналы.
3. `ranker` — та же логика scoring и priority, без изменений.
4. `advisor` — та же rule-based система правил.

Контракт API при этом **не меняется**.
