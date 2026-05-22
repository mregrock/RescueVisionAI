# RescueVisionAI — Frontend

Веб-приложение спасателя для учебного MVP. React + Vite + TypeScript + Tailwind CSS.

Что умеет:

- **Главный экран** — выбор demo-сценария → `POST /api/v1/analyze` → отрисовка
  общего риска, уверенности AI, наблюдений сцены, карточек пострадавших,
  чеклиста рекомендованных действий и применимых протоколов.
- **Протоколы** — список (`GET /api/v1/protocols`) и детальная страница каждого
  протокола (`GET /api/v1/protocols/{id}`). Ссылки на протоколы есть прямо в
  результате анализа и в карточках пострадавших.
- **Камера (real-режим)** — снимок с устройства → `POST /api/v1/analyze/image`
  (multipart), тот же экран результата. Работает на `localhost` и HTTPS.
- **Backend status** — индикатор в шапке периодически дёргает `/api/v1/health`.

UX:

- Крупные кнопки, цветовая кодировка статусов (зелёный / жёлтый / оранжевый /
  красный), критичные действия подсвечены красным.
- Адаптив под телефон (single column на узком, две колонки на `sm:`+).
- Понятные сообщения об ошибках с кнопкой «Повторить».

## Требования

- Node.js 18+ (LTS 20 рекомендуется)
- Запущенный backend на `http://localhost:8000` (см. корневой `README.md`)

## Установка и запуск

```bash
cd frontend
npm install
npm run dev
```

Откройте `http://localhost:5173`. Vite сам поднимет dev-сервер с горячей
перезагрузкой.

Сборка прод-версии:

```bash
npm run build
npm run preview
```

## Конфигурация

Переменные окружения читаются из `.env` (см. `.env.example`):

| Переменная           | Дефолт                  | Назначение                       |
| -------------------- | ----------------------- | -------------------------------- |
| `VITE_API_BASE_URL`  | `http://localhost:8000` | Базовый URL backend (без `/api`) |

Создать локальный `.env`:

```bash
cp .env.example .env
# при необходимости поменяйте URL
```

## Запуск вместе с backend

В двух терминалах из корня репозитория:

Терминал 1 — backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Терминал 2 — frontend:

```bash
cd frontend
npm install
npm run dev
```

После этого открыть `http://localhost:5173`. В шапке должен светиться зелёный
индикатор `backend online`. Если он красный — проверьте, что backend поднят
на `:8000` и CORS открыт (по умолчанию `RVA_CORS_ORIGINS=["*"]`).

## Структура

```
src/
├── api/
│   ├── client.ts      # fetch-обёртка, обработка ошибок (ApiError)
│   └── types.ts       # TS-типы по docs/api-contract.md
├── components/
│   ├── Layout.tsx     # хедер + навигация + футер
│   ├── BackendStatus.tsx
│   ├── ScenarioSelector.tsx
│   ├── RiskBadge.tsx
│   ├── VictimCard.tsx
│   ├── ActionChecklist.tsx
│   ├── AnalysisResult.tsx
│   └── states.tsx     # LoadingView, ErrorView, Spinner
├── pages/
│   ├── AnalyzePage.tsx          # /
│   ├── ProtocolsListPage.tsx    # /protocols
│   ├── ProtocolDetailPage.tsx   # /protocols/:id
│   └── CameraPage.tsx           # /camera (real-режим)
├── utils/
│   ├── ids.ts         # генерация incident_id
│   └── labels.ts      # русские подписи и стили под цвета риска
├── App.tsx
├── main.tsx
└── index.css
```

## Соответствие demo checklist

- [x] Frontend открывается, селектор сценариев работает.
- [x] Для `single_unconscious` отображается красный `Critical`.
- [x] Для `multiple_victims` рисуются карточки с разными приоритетами.
- [x] Для `severe_bleeding` критичные действия выделены красным.
- [x] Для `low_confidence` показывается жёлтое предупреждение.
- [x] На каждой странице с результатом отображается `disclaimer`.
- [x] Страница протоколов открывает любой протокол по id.

## Safety

Все рекомендации — справочные. Финальное решение всегда принимает спасатель.
Эта формулировка приходит с backend в поле `disclaimer` и всегда показывается
на экране результата.
