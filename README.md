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
| AI (MVP) | Mock / rule-based модуль, далее — YOLOv8 + классификатор |
| Очередь / кэш | Redis (на этапе расширения) |
| Хранилище | PostgreSQL + MinIO (на этапе расширения) |
| Инфраструктура | Docker + Docker Compose |

На этапе MVP backend возвращает результат **синхронно**, без Celery/Redis/БД, чтобы не блокировать команду на инфраструктуре.

---

## Quick start (backend)

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

curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"incident_id":"inc-001","rescuer_id":"resc-42","scenario":"single_unconscious"}'

curl http://localhost:8000/api/v1/protocols
```

### Запуск через Docker

```bash
docker build -t rescue-vision-ai-backend -f backend/Dockerfile .
docker run --rm -p 8000:8000 rescue-vision-ai-backend
```

Или через Docker Compose:
```bash
docker-compose up --build
```

### Тесты и линтер

```bash
pip install -r backend/requirements-dev.txt

pytest                       # тесты (конфиг в pyproject.toml)
ruff check backend           # линтер
ruff format backend          # автоформат
```

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
- Backend FastAPI с 4 endpoints и стабильным API-контрактом.
- Mock AI-модуль, возвращающий правдоподобный анализ по сценарию.
- Файл [`protocols.json`](protocols.json) с базовыми медицинскими протоколами.

В MVP **не входит**:

- Реальная обработка изображений (YOLO/CV).
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
