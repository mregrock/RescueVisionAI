# Roadmap

План реализации RescueVisionAI на 4 недели + MVP-фокус и demo checklist. Документ намеренно короткий — это рабочий план, а не отчёт.

---

## MVP goals

К концу разработки команда должна показать **рабочее end-to-end demo**:

1. Открыли веб-приложение спасателя.
2. Выбрали demo-сценарий.
3. Нажали «Анализ».
4. Получили JSON от backend → увидели пострадавших, риски и рекомендации.
5. Перешли на страницу протоколов и открыли один из них.

Всё должно работать **локально**, без интернета и внешних сервисов.

---

## Sprint 0: kickoff (день 1)

- [x] Согласовать архитектуру — см. [`docs/architecture.md`](architecture.md).
- [x] Зафиксировать API-контракт — см. [`docs/api-contract.md`](api-contract.md).
- [x] Зафиксировать triage-правила — см. [`docs/ai-triage-rules.md`](ai-triage-rules.md).
- [x] Распределить роли — см. [`docs/roles-and-scope.md`](roles-and-scope.md).
- [ ] Инициализировать репозиторий и базовые папки `backend/`, `frontend/`.

---

## Week 1 — каркас

Цель: «всё запускается, ничего полезного не делает».

**Backend**

- [ ] FastAPI-проект, `uvicorn`, CORS, Swagger.
- [ ] Endpoint `GET /api/v1/health`.
- [ ] Заглушка `POST /api/v1/analyze`, возвращающая фиксированный JSON.

**Frontend**

- [ ] React + Vite + Tailwind инициализация.
- [ ] Главный экран: селектор сценария + кнопка «Анализ».
- [ ] API-клиент, дергающий `/health` и `/analyze` (или mock JSON).

**AI**

- [ ] Скелет модуля `backend/ai/` с функцией `analyze(scenario)`.
- [ ] Black-list безопасных формулировок.
- [ ] Черновик [`protocols.json`](../protocols.json) (минимум 3 протокола).

---

## Week 2 — полезная функциональность

Цель: «по сценарию выдаётся осмысленный результат».

**Backend**

- [ ] Полная Pydantic-схема `/analyze`.
- [ ] Интеграция с AI-модулем.
- [ ] Endpoints `/protocols` и `/protocols/{id}`.

**Frontend**

- [ ] Карточки пострадавших с severity / status / priority / signals.
- [ ] Чеклист `recommended_actions` с возможностью отмечать пункты.
- [ ] Цветовая кодировка статусов.
- [ ] Loading / error состояния.

**AI**

- [ ] Реализация scoring по всем сигналам.
- [ ] Маппинги score → severity → status → priority.
- [ ] Все 4 сценария возвращают корректный результат.
- [ ] Полный [`protocols.json`](../protocols.json) (все 7 протоколов).

---

## Week 3 — UX и интеграция

Цель: «выглядит и ощущается как ассистент спасателя».

**Frontend**

- [ ] Страница `/protocols` со списком и деталями.
- [ ] Полировка UI: крупные кнопки, контраст, мобильный layout.
- [ ] Отображение `confidence`, `quality.low_confidence`, `disclaimer`.

**Backend**

- [ ] Обработка ошибок и 422.
- [ ] Логирование запросов.
- [ ] Тесты на 4 сценария (smoke).

**AI**

- [ ] Точная подстройка score, чтобы overall_risk совпадал с ожиданиями таблицы сценариев.
- [ ] Финальная редактура формулировок.

---

## Week 4 — тестирование, demo, документация

Цель: «готово к показу».

- [ ] End-to-end прогон по всем 4 сценариям.
- [ ] Запись короткого demo-видео или live-демо.
- [ ] Обновлённый [`README.md`](../README.md) с инструкцией запуска.
- [ ] Опционально: Docker Compose, чтобы поднять всё одной командой.
- [ ] Подготовка слайдов / защиты.

---

## Risks

| Риск | Митигация |
|---|---|
| Backend задерживается — frontend без данных | Frontend держит локальный mock JSON в формате API-контракта |
| AI-логика «течёт» в backend | Чёткая граница: backend вызывает `analyze(scenario)`, не знает деталей |
| Разные представления о JSON у frontend и backend | Источник истины — [`docs/api-contract.md`](api-contract.md), любые правки только через него |
| Формулировки звучат как медицинский диагноз | Чек-лист безопасных формулировок в [`docs/ai-triage-rules.md`](ai-triage-rules.md) |
| Не хватает времени на полировку | Сначала закрываем все 4 сценария, потом UX |

---

## Phase 1 — Real AI integration

Цель: заменить mock-`detector` на реальную инференцию по кадру. Mock-режим сохраняется параллельно для demo и unit-тестов.

**Backend**

- [ ] Расширить `AnalyzeRequest` полем `frame: str | None` (base64), валидация "scenario XOR frame".
- [ ] Подпакет `backend/ai/real/` с разделёнными модулями: `frame_decoder`, `filter`, `pose`, `blood`, `signal_extractor`.
- [ ] `detector.real(frame)` собирает `RawScene` + `RawVictim[]` из реального инференса.
- [ ] DI: `get_analyzer()` возвращает real- или mock-реализацию в зависимости от того, что пришло в запросе.
- [ ] Тесты на real pipeline с фикстурами (положить пару JPEG в `backend/tests/fixtures/`).
- [ ] Бенчмарк времени отклика; если медленно — кеш моделей в памяти, optional warmup на старте.

**AI**

- [ ] Выбор моделей: YOLOv8n (filter) + YOLOv8n-pose (pose). Альтернатива: VLM, решение задокументировать.
- [ ] Правила signal extractor: keypoints → `lying / sitting / standing`, multi-frame → `no_movement / weak_movement`.
- [ ] Blood detection через OpenCV HSV-маску по bbox.
- [ ] (Опц.) Frame deduplication через perceptual hash.

**Frontend**

- [ ] Страница с `<video>` + `<canvas>`: получение камеры через `getUserMedia`, снимок раз в 1-2 секунды.
- [ ] Отправка кадра на `POST /analyze` как base64, отображение результата в реальном времени.
- [ ] Переключатель "demo (scenario) / real (camera)" — для тех, у кого нет камеры на устройстве.

**Инфраструктура**

- [ ] `ultralytics` + `opencv-python` в `backend/requirements.txt`.
- [ ] Веса моделей не коммитим — скачиваются `ultralytics` при первом запуске.
- [ ] Docker-образ — учесть, что модели подтянутся при первом старте контейнера, или предзагрузить в Dockerfile.

---

## Phase 2+ (за пределами учебного этапа)

- Realtime через WebSocket / RTSP.
- Очередь кадров (Redis Streams) + отдельный AI Worker.
- PostgreSQL для инцидентов и истории, MinIO/S3 для кадров.
- Multi-frame анализ движения и трендов.
- Авторизация спасателей и штаба.

---

## Demo checklist

Прогоняем перед защитой:

- [ ] Backend стартует без ошибок (`uvicorn` / Docker).
- [ ] `GET /api/v1/health` → `{ "status": "ok" }`.
- [ ] `POST /api/v1/analyze` отрабатывает на все 4 сценария.
- [ ] `GET /api/v1/protocols` возвращает 7 протоколов.
- [ ] `GET /api/v1/protocols/basic_life_support` возвращает шаги.
- [ ] Frontend открывается, селектор сценариев работает.
- [ ] Для `single_unconscious` отображается красный Critical.
- [ ] Для `multiple_victims` отображается 3 карточки с разными приоритетами.
- [ ] Для `severe_bleeding` подсвечивается рекомендация остановить кровотечение.
- [ ] Для `low_confidence` отображается предупреждение о низкой уверенности.
- [ ] На экране везде присутствует `disclaimer`.
- [ ] Страница протоколов открывается, можно посмотреть любой протокол.

Когда все галочки стоят — MVP готов.
