# Team Roles

В команде 3 человека. Документ фиксирует **зоны ответственности**, **deliverables** и **точки интеграции**. Цель — чтобы никто не блокировал друг друга и не делал одну и ту же работу дважды.

---

## Roles overview

| Role | Owns | Inputs | Outputs |
|---|---|---|---|
| Frontend / Product | UI, UX, состояния, рендеринг результата | API-контракт | Веб-приложение спасателя |
| Backend / API | Endpoints, схемы, валидация, оркестрация | AI-функции и protocols.json | Стабильный JSON API |
| AI / Triage / Protocols | Mock-логика анализа, scoring, рекомендации | Сценарий + scene signals | Структурированный анализ + protocols.json |

---

## 1. Frontend / Product

### Owns

- React + Vite + Tailwind приложение.
- Главный экран спасателя.
- Страница протоколов.
- API-клиент (fetch / axios).
- Mock-режим на случай, если backend ещё не готов.

### Deliverables

- Главный экран:
  - выбор demo-сценария (`single_unconscious`, `multiple_victims`, `severe_bleeding`, `low_confidence`);
  - кнопка «Запустить анализ»;
  - loading-состояние;
  - error-состояние с понятным сообщением;
  - блок с результатом:
    - общий риск (цветная плашка),
    - confidence,
    - количество людей,
    - наблюдения сцены,
    - карточки пострадавших с priority / severity / status / bbox / признаками,
    - чеклист рекомендаций с возможностью отмечать выполненные пункты,
    - список применимых протоколов с переходом на их описание.
- Страница `/protocols`:
  - список из `GET /api/v1/protocols`;
  - детальная страница протокола из `GET /api/v1/protocols/{id}`.
- UX-требования:
  - крупные кнопки;
  - цветовая кодировка статусов (зелёный/жёлтый/оранжевый/красный);
  - минимум текста;
  - критичные действия — красные.

### Not in scope

- Backend / AI логика.
- Авторизация.
- Карта / GPS-визуализация (можно опционально, если хватает времени).
- Реальная работа с камерой.

---

## 2. Backend / API

### Owns

- FastAPI-приложение, CORS, Swagger.
- Endpoints `/health`, `/analyze`, `/protocols`, `/protocols/{id}`.
- Pydantic-схемы запросов и ответов.
- Слой `services/`, который вызывает AI-модуль.
- Подключение [`protocols.json`](../protocols.json).

### Структура кода

```
backend/
├── api/
│   ├── health.py
│   ├── analyze.py
│   └── protocols.py
├── schemas/
│   ├── analyze.py
│   └── protocols.py
├── services/
│   ├── analyze_service.py
│   └── protocols_service.py
├── ai/                # подключает модуль AI-роли
│   └── __init__.py
└── main.py
```

### Deliverables

- Запускаемое приложение (`uvicorn main:app --reload`).
- Все 4 endpoints, соответствующие [`docs/api-contract.md`](api-contract.md).
- Валидация входных данных через Pydantic.
- Swagger по адресу `/docs`.
- Стабильный JSON, не зависящий от внутренностей AI.

### Not in scope

- Реальная AI-модель.
- Очереди, БД, S3.
- Авторизация, rate limiting.
- WebSocket / push.

---

## 3. AI / Triage / Protocols

### Owns

- Mock AI-модуль (Python).
- Файл [`protocols.json`](../protocols.json).
- Triage-логика: signals → score → severity / priority.
- Rule-based генератор рекомендаций.
- Безопасные формулировки и disclaimer.

### Структура кода

```
backend/ai/
├── detector.py     # mock: возвращает scene + signals по сценарию
├── classifier.py   # mock: сигналы → severity_score / label
├── ranker.py       # сортировка по score, priority
├── advisor.py      # rule-based рекомендации и first_aid
└── scenarios.py    # blueprints по 4 сценариям
```

### Deliverables

- Функция уровня модуля, например `analyze(scenario: str) -> AnalysisResult`, которую вызывает backend.
- Поддержка всех 4 сценариев согласно [`docs/ai-triage-rules.md`](ai-triage-rules.md).
- Корректный mapping score → severity → status → priority.
- Файл [`protocols.json`](../protocols.json) с протоколами:
  - `scene_safety`
  - `primary_assessment`
  - `basic_life_support`
  - `severe_bleeding`
  - `burns`
  - `fractures`
  - `mass_casualty_triage`
- Формулировки соответствуют требованиям безопасности (см. раздел Safety в [`docs/ai-triage-rules.md`](ai-triage-rules.md)).

### Not in scope

- Реальные модели YOLO / ResNet.
- Обучение моделей.
- Frontend-рендеринг.
- API-роутинг.

---

## Integration points

### Frontend ↔ Backend

- Контракт: [`docs/api-contract.md`](api-contract.md).
- На время отсутствия backend frontend использует **локальный mock JSON** того же формата.
- Любые изменения формата ответа должны быть зафиксированы в `api-contract.md` **до** реализации.

### Backend ↔ AI

- Backend вызывает функцию из `backend/ai/`, например:

  ```python
  from backend.ai import analyze
  result = analyze(scenario="single_unconscious")
  ```

- `result` — Python-структура, которую backend сериализует в Pydantic-схему ответа `/analyze`.
- AI-роль гарантирует **детерминированность** результата для одного и того же сценария.

### Все ↔ Protocols

- Единственный источник истины по протоколам — [`protocols.json`](../protocols.json), его собирает AI-роль.
- Backend читает его и отдаёт через `/protocols` и `/protocols/{id}`.
- Frontend показывает список и детали.

---

## Definition of done

Команда считает MVP готовым, когда:

- Frontend запускается локально, выбирает сценарий и показывает результат анализа.
- Backend отдаёт 200 на `/analyze` для всех 4 сценариев с корректным JSON.
- Все 4 endpoint работают и доступны в Swagger.
- `protocols.json` содержит все 7 протоколов, отдаётся через API и отображается на frontend.
- В ответе `/analyze` присутствует `disclaimer`.
- Demo-сценарий проходит end-to-end без ошибок.

---

## Communication & sync

- Любое изменение API → правка [`docs/api-contract.md`](api-contract.md) → уведомление команды.
- Любое изменение логики AI → правка [`docs/ai-triage-rules.md`](ai-triage-rules.md).
- Любое изменение в структуре протоколов → правка [`protocols.json`](../protocols.json) и согласование с frontend.
