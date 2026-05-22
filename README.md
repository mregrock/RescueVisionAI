# RescueVisionAI

AI-ассистент для спасателей МЧС, который анализирует кадры с места ЧС, оценивает состояние пострадавших, выставляет приоритеты спасения и подсказывает спасателю последовательность действий в реальном времени.

Проект разрабатывается в рамках курса «Основы проектирования медицинских систем».

---

## What it does

- Принимает кадр (или demo-сценарий) и метаданные от спасателя.
- Детектирует пострадавших и оценивает их состояние (severity).
- Ранжирует пострадавших по приоритету спасения.
- Выдаёт rule-based рекомендации первой помощи и применимые протоколы.
- Возвращает структурированный JSON для отображения в UI спасателя и панели штаба.

Главная идея — **не заменить** решение спасателя, а **ускорить и поддержать** его в условиях стресса и нехватки времени.

---

## Demo scenarios

В рамках MVP поддерживаются 4 demo-сценария (передаются в `POST /api/v1/analyze`):

| Scenario | Описание |
|---|---|
| `single_unconscious` | Один пострадавший без сознания, лежит, без видимых движений |
| `multiple_victims` | Несколько пострадавших на сцене, требуется массовая сортировка |
| `severe_bleeding` | Пострадавший с видимым сильным кровотечением |
| `low_confidence` | Плохое качество кадра (дым/темнота), AI не уверен в оценке |

---

## Tech stack

| Слой | Технологии |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend / API | FastAPI (Python), Pydantic, Uvicorn |
| AI | YOLOv8n (фильтр кадров) + YOLOv8n-pose (детекция + поза), rule-based scoring |
| Очередь / кэш | Redis (на этапе расширения) |
| Хранилище | PostgreSQL + MinIO (на этапе расширения) |
| Инфраструктура | Docker + Docker Compose |

На этапе MVP backend возвращает результат **синхронно**, без Celery/Redis/БД, чтобы не блокировать команду на инфраструктуре.

---

## Quick start (всё одной командой)

Frontend + backend в Docker Compose:

```bash
docker compose up --build
```

После старта:

- **Frontend (UI спасателя):** http://localhost:8080
- **Backend Swagger:** http://localhost:8000/docs
- **Backend health:** http://localhost:8000/api/v1/health

Фронт собирается в production (vite build), отдаётся через nginx, который
проксирует `/api/*` на backend — всё работает в одной compose-сети без CORS.
Frontend запускается после того, как backend ответил `healthcheck`.

Остановить:

```bash
docker compose down
```

---

## Quick start (backend отдельно, dev-режим)

Требуется Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

uvicorn backend.main:app --reload
```

Сервис поднимется на `http://localhost:8000`, Swagger UI — на `http://localhost:8000/docs`.

Быстрая проверка:

```bash
curl http://localhost:8000/api/v1/health

# Mock-режим (demo-сценарий)
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"incident_id":"inc-001","rescuer_id":"resc-42","scenario":"single_unconscious"}'

# Real-режим (реальный кадр)
curl -X POST http://localhost:8000/api/v1/analyze/image \
  -F "image=@/path/to/photo.jpg" \
  -F "incident_id=inc-001" \
  -F "rescuer_id=resc-42"

curl http://localhost:8000/api/v1/protocols
```

### Конфигурация через env

Все настройки лежат в `backend/config.py` (`Settings(BaseSettings)`) и переопределяются env-переменными с префиксом `RVA_`. Файл `.env` в корне проекта подхватывается автоматически.

| Переменная | Дефолт | Назначение |
|---|---|---|
| `RVA_SERVICE_NAME` | `rescue-vision-ai` | Имя сервиса в `/health` |
| `RVA_SERVICE_VERSION` | `0.1.0` | Версия в `/health` и Swagger |
| `RVA_LOG_LEVEL` | `INFO` | Уровень логирования |
| `RVA_CORS_ORIGINS` | `["*"]` | Список разрешённых origins (JSON-массив) |
| `RVA_PROTOCOLS_PATH` | `<repo>/protocols.json` | Путь к файлу протоколов |

Пример `.env` для прода:

```
RVA_CORS_ORIGINS=["https://app.example.com"]
RVA_LOG_LEVEL=WARNING
```

### Запуск через Docker

Только backend:

```bash
docker build -t rescue-vision-ai-backend -f backend/Dockerfile .
docker run --rm -p 8000:8000 rescue-vision-ai-backend
```

Backend + frontend вместе (см. секцию «Quick start» в начале):

```bash
docker compose up --build
```

### Тесты и линтер

```bash
pip install -r backend/requirements-dev.txt

pytest                       # тесты (конфиг в pyproject.toml)
ruff check backend           # линтер
ruff format backend          # автоформат
```

### Pre-commit

После клонирования один раз ставим хуки:

```bash
pip install -r backend/requirements-dev.txt
pre-commit install
```

Дальше при каждом `git commit` автоматически прогоняются `ruff check --fix`, `ruff format`, удаление trailing-whitespace и т.п. Это страхует от того, что CI упадёт на форматировании.

Прогнать вручную по всем файлам:

```bash
pre-commit run --all-files
```

### CI

GitHub Actions workflow `.github/workflows/backend-ci.yml` на каждый push в `main` и PR прогоняет `ruff check`, `ruff format --check` и `pytest`. Зелёный CI — обязательное условие для merge.

---

## Documentation map

| Документ | О чём |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Архитектура, компоненты, поток данных, альтернативные сценарии |
| [`docs/api-contract.md`](docs/api-contract.md) | Контракт API между frontend и backend |
| [`docs/ai-triage-rules.md`](docs/ai-triage-rules.md) | Triage-логика: scoring, severity, priority, recommendations |
| [`docs/roles-and-scope.md`](docs/roles-and-scope.md) | Распределение ролей и зон ответственности |
| [`docs/roadmap.md`](docs/roadmap.md) | План реализации по неделям и demo checklist |

---

## MVP scope

В MVP входит:

- Frontend с выбором demo-сценария и отображением результата анализа.
- Backend FastAPI с 5 endpoints и стабильным API-контрактом.
- Mock AI-модуль, возвращающий правдоподобный анализ по сценарию (`POST /analyze`).
- Real AI-модуль на базе YOLOv8n + YOLOv8n-pose для анализа реальных кадров (`POST /analyze/image`).
- Файл [`protocols.json`](protocols.json) с базовыми медицинскими протоколами.

В MVP **не входит**:

- Очереди, БД, S3-хранилище.
- Авторизация и продакшен-инфраструктура.
- Мобильное приложение (используется веб-интерфейс).

---

## Team

Команда из 3 человек:

1. **Frontend / Product** — React-приложение спасателя.
2. **Backend / API** — FastAPI, контракт API.
3. **AI / Triage / Protocols** — mock-логика анализа и протоколы.

Подробнее — в [`docs/roles-and-scope.md`](docs/roles-and-scope.md).

---

## Safety disclaimer

Система носит **вспомогательный характер**. Все рекомендации формулируются осторожно: «возможна критическая ситуация», «проверьте согласно протоколу». Финальное решение всегда принимает спасатель.
