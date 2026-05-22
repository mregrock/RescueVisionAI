# Roadmap

План реализации RescueVisionAI по этапам и demo checklist.

Главный документ по AI-пайплайну: [`docs/ai-pipeline-v2.md`](ai-pipeline-v2.md).

---

## MVP goals

К концу разработки команда должна показать **рабочее end-to-end demo**:

1. Открыли веб-приложение спасателя.
2. **Demo сценарий:** выбрали один из 4 mock-сценариев → получили структурированный анализ → увидели пострадавших, риски, рекомендации, протоколы.
3. **Real сценарий:** сделали снимок (или серию снимков) с камеры → AI определил позу пострадавших → triage-движок по протоколу START выдал severity и рекомендации.
4. Перешли на страницу протоколов и открыли любой из них.

Всё работает **локально**, без интернета и внешних сервисов.

---

## Sprint 0: kickoff (день 1) — DONE

- [x] Архитектура — см. [`docs/architecture.md`](architecture.md).
- [x] API-контракт — см. [`docs/api-contract.md`](api-contract.md).
- [x] Triage-правила v1 — см. [`docs/ai-triage-rules.md`](ai-triage-rules.md).
- [x] Распределение ролей — см. [`docs/roles-and-scope.md`](roles-and-scope.md).
- [x] Инициализированы папки `backend/` и `frontend/`.

---

## Phase 0 — Каркас и mock-режим (DONE)

Цель: «всё запускается, mock работает для всех 4 сценариев».

**Backend (DONE)**
- [x] FastAPI, CORS, Swagger, pydantic-settings.
- [x] `GET /api/v1/health`.
- [x] `POST /api/v1/analyze` по сценарию.
- [x] `GET /api/v1/protocols`, `GET /api/v1/protocols/{id}`.
- [x] Полная Pydantic-схема ответа.
- [x] Тесты, ruff, pre-commit, CI, Dockerfile, docker-compose.

**Frontend (DONE)**
- [x] React + Vite + TypeScript + Tailwind.
- [x] Главный экран: селектор 4 сценариев + кнопка анализа.
- [x] Loading / error / success состояния.
- [x] Карточки пострадавших с severity, status, priority, signals.
- [x] Чеклист `recommended_actions` с возможностью отмечать.
- [x] Цветовая кодировка статусов (зелёный/жёлтый/оранжевый/красный).
- [x] Страница `/protocols` (список) и `/protocols/:id` (детали).
- [x] Индикатор `backend status` по `/health`.
- [x] Real-режим: страница `/camera` с `getUserMedia` + snapshot → `POST /analyze/image`.
- [x] Адаптив под телефон.

**AI (DONE — v1, mock + heuristic real)**
- [x] Mock-модуль `backend/ai/` с поддержкой 4 сценариев.
- [x] Полный `protocols.json` (7 протоколов).
- [x] Real-режим v1: YOLOv8n + YOLOv8n-pose + эвристики на keypoints + HSV.

---

## Phase 1 — AI Pipeline v2 (CURRENT)

Цель: заменить эвристики v1 на **обученную нами модель + классический CV + формализованный медицинский triage-протокол**.

Детальный план — в [`docs/ai-pipeline-v2.md`](ai-pipeline-v2.md). Здесь — только milestones и галочки.

### Зачем переписываем v1

v1 на эвристиках работает на demo-сценариях (mock), но **разваливается на реальных кадрах**: классифицирует стоящих как лежащих, ставит «без сознания» при низкой уверенности, HSV-маски ложно срабатывают на коже и фоне. Подробности — в [`docs/ai-pipeline-v2.md`](ai-pipeline-v2.md).

### Этап A — Pose Classifier MLP (3-4 дня) — AI-роль

Главная «наша нейросеть»: маленькая MLP, обученная на keypoints от YOLO-pose, классифицирует позу в `{standing, sitting, lying, falling}`.

- [ ] `prepare_dataset.py`: NTU RGB+D / MPII / Roboflow → JSONL с keypoints + метками.
- [ ] Собран датасет ≥ 2000 размеченных примеров.
- [ ] `model.py`: MLP-архитектура (51→64→32→4).
- [ ] `train_pose_classifier.py`: training loop, early stopping, метрики.
- [ ] Целевые метрики: accuracy ≥ 0.85, F1 macro ≥ 0.80, recall(lying) ≥ 0.90.
- [ ] Jupyter notebook с полным процессом обучения + confusion matrix.
- [ ] Веса в `backend/ai/weights/pose_classifier.pth`.
- [ ] Интеграция: `backend/ai/pose_classifier.py` заменяет `signal_extractor::_pose_signals`.
- [ ] Тесты на inference.

### Этап B — START Triage Engine (1-2 дня) — AI или Backend

Реализация международного протокола FEMA для triage. Заменяет линейную сумму весов.

- [ ] Изучить START guidelines (FEMA, CHEMM).
- [ ] `backend/ai/triage_engine.py` с decision tree.
- [ ] Confidence gate: при `pose_confidence < 0.5` → max severity = medium.
- [ ] Mapping START categories (RED/YELLOW/GREEN/BLACK) → наш API (low/medium/high/critical).
- [ ] ~20 unit-тестов на все комбинации (pose, motion, confidence).
- [ ] Mermaid-диаграмма decision tree в `docs/ai-triage-rules.md`.
- [ ] Интеграция в `backend/ai/__init__.py::analyze_image()`.

### Этап C — Motion Analysis (2-3 дня) — опционально

Оптический поток для определения отсутствия движения (главный сигнал бессознательного состояния).

- [ ] `backend/ai/motion.py`: `cv2.calcOpticalFlowFarneback` per bbox.
- [ ] Bbox tracking между кадрами по IoU.
- [ ] Mapping в `{no_movement, weak_movement, active_movement}`.
- [ ] API: поддержка multipart с несколькими файлами в `POST /analyze/image` (backwards-compatible).
- [ ] Frontend: burst capture mode (5 кадров за 1 секунду).
- [ ] Toggle «single shot / burst» на `/camera`.

### Этап D — Документация и защита (1 день)

- [ ] Обновить `docs/architecture.md` под v2 pipeline.
- [ ] Обновить `docs/ai-triage-rules.md` под START.
- [ ] Обновить `backend/ai/README.md`.
- [ ] Обновить root `README.md` (tech stack, инструкции).
- [ ] Слайды защиты с метриками модели и архитектурой.
- [ ] Demo-сценарий записать на видео (бэкап на случай если на защите backend упадёт).

---

## Phase 2+ (за пределами учебного этапа)

- **Visual signs CNN** — отдельная обученная нами CNN на размеченных медицинских кадрах для детекции `bleeding_visible`, `burns_visible`, `multiple_injuries`. Требует партнёрства с медучилищем для разметки. Большой scope.
- **Multi-frame tracking** — устойчивое сопровождение пострадавших между кадрами для history-aware triage.
- **Realtime через WebSocket** — streaming кадров вместо запрос-ответ.
- **Очередь кадров (Redis Streams), AI Worker** как отдельный процесс.
- **PostgreSQL** для инцидентов, **MinIO/S3** для кадров.
- **Авторизация** спасателей и штаба.
- **Mobile native app** (React Native / Flutter) для полевых условий.
- **GPS-карта в штабе** с realtime-позициями спасателей.

---

## Risks (актуальные на Phase 1)

| Риск | Митигация |
|---|---|
| Не находится подходящего pose-датасета | Fallback: ручная разметка 200 примеров за вечер. Минимально жизнеспособно. |
| MLP не дотягивает до F1=0.85 | Эксперименты с LSTM/Transformer + аугментация. В крайнем случае — fallback на эвристики при низкой уверенности. |
| Motion analysis не успеваем | Опциональный компонент. v2 без него работает (motion=unknown). |
| На защите спросят «почему не сами обучили YOLO» | См. FAQ в [`docs/ai-pipeline-v2.md`](ai-pipeline-v2.md). |
| Real-режим упадёт на демо | Mock-режим работает идеально и закрывает demo checklist. Real показываем «во вторую очередь». |
| Backend не запустится на железе комиссии | Demo-видео записано заранее как бэкап. |

---

## Demo checklist

Прогоняем перед защитой:

**Backend:**
- [ ] `uvicorn backend.main:app` стартует без ошибок.
- [ ] `GET /api/v1/health` → `{ "status": "ok" }`.
- [ ] `POST /api/v1/analyze` отрабатывает на все 4 сценария.
- [ ] `GET /api/v1/protocols` возвращает 7 протоколов.
- [ ] `GET /api/v1/protocols/basic_life_support` возвращает шаги.

**Frontend:**
- [ ] Открывается на `localhost:5173`.
- [ ] Индикатор `backend online` зелёный.
- [ ] Селектор сценариев работает.
- [ ] Для `single_unconscious` отображается красный `Critical`.
- [ ] Для `multiple_victims` рисуются 3 карточки с разными приоритетами.
- [ ] Для `severe_bleeding` критичные действия выделены красным.
- [ ] Для `low_confidence` показывается жёлтое предупреждение.
- [ ] Везде присутствует `disclaimer`.
- [ ] Страница протоколов открывается, можно посмотреть любой.

**Real-режим (Phase 1 / v2):**
- [ ] `/camera` запрашивает камеру, видео отображается.
- [ ] Снимок отправляется на `POST /analyze/image`.
- [ ] Для стоящего человека → `severity = low`, pose = `standing`.
- [ ] Для лежащего на полу человека → `severity = high` или `critical`, pose = `lying`.
- [ ] `confidence` отображается и адекватен реальной уверенности модели.
- [ ] При неудачной классификации → `quality.low_confidence = true` с понятным предупреждением.

**Защита:**
- [ ] Notebook с обучением модели открывается.
- [ ] Метрики на test set приложены в README.
- [ ] Confusion matrix показывает разумное распределение ошибок.
- [ ] START guidelines процитированы с источниками.

Когда все галочки стоят — MVP готов.

---

## Documentation map

| Документ | О чём |
|---|---|
| [`docs/architecture.md`](architecture.md) | Архитектура системы, компоненты, поток данных |
| [`docs/api-contract.md`](api-contract.md) | Контракт API между frontend и backend (стабилен) |
| [`docs/ai-pipeline-v2.md`](ai-pipeline-v2.md) | **Главный документ по новому AI-пайплайну** |
| [`docs/ai-triage-rules.md`](ai-triage-rules.md) | Triage-правила (v1; обновляется под START в Phase 1) |
| [`docs/roles-and-scope.md`](roles-and-scope.md) | Распределение ролей |
| [`docs/roadmap.md`](roadmap.md) | План реализации и demo checklist (этот документ) |
