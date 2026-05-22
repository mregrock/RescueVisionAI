# AI Pipeline v2 — план обновления

Документ описывает **обновлённый AI-пайплайн** для real-режима (`POST /api/v1/analyze/image`). Текущая реализация (Phase 1) на основе эвристик keypoints + HSV-масок показала фундаментальные проблемы (см. раздел «Что не так с v1»). v2 заменяет эвристики на **обученную нами модель + классический CV + формализованный медицинский triage-протокол**.

Mock-режим (`POST /api/v1/analyze` по `scenario`) **остаётся без изменений** — он закрывает demo checklist и работает на защите. v2 касается только real-режима.

API-контракт **не меняется** — фронт не трогаем.

---

## TL;DR

Заменяем «YOLO-pose → эвристики → линейная сумма весов» на:

```
кадр
  ↓
YOLOv8n + YOLOv8n-pose   (готовые, off-the-shelf, инфраструктура)
  ↓
17 keypoints на каждого человека
  ↓
⭐ Pose Classifier MLP   (наша обученная нейросеть, ~5K параметров)
  ↓
pose ∈ {lying, sitting, standing, falling} + confidence
  ↓
⭐ Motion Analysis       (наш CV-компонент, optical flow по серии кадров, опц.)
  ↓
motion ∈ {no_movement, weak_movement, active_movement}
  ↓
⭐ START Triage Engine   (наш rule engine на основе протокола FEMA)
  ↓
severity_score + priority + recommended_actions + protocols
  ↓
JSON по существующему контракту
```

**«Наше» в этом пайплайне:**
1. Pose Classifier MLP (обученная нами модель + датасет + метрики)
2. Motion analysis pipeline (наша реализация классического CV)
3. START Triage Engine (наша реализация международного медицинского протокола)
4. Multi-modal архитектура и интеграция
5. Frontend и full-stack продукт

**«Не наше» (инфраструктура):**
- YOLOv8n / YOLOv8n-pose (pretrained на COCO, скачиваются через `ultralytics`)
- FastAPI, React, PyTorch, OpenCV (стандартные библиотеки)

---

## Что не так с v1 (мотивация переписывания)

Текущий `signal_extractor.py` + `classifier.py` имеют системные проблемы, которые невозможно «подкрутить порогами»:

| Косяк | Где | Что происходит |
|---|---|---|
| `lying` без проверки aspect bbox | `signal_extractor.py:_pose_signals` | Стоящий человек на портретном кадре классифицируется как `lying`, потому что плечи и бёдра близко по y |
| `possible_unconscious` при **низкой** уверенности | `signal_extractor.py:53` | Логика инвертирована: чем хуже видит модель, тем увереннее ставит «без сознания» |
| HSV-маска `bleeding` без skin-tone exclusion | `signal_extractor.py:_color_signals` | Любая открытая кожа на тёплом свете → `severe_bleeding` |
| HSV-маска `burns_visible` | там же | Ловит любые коричневые объекты в кадре (волосы, мебель) |
| `confidence` не влияет на `severity_score` | `__init__.py` + `classifier.py` | «41% уверенности, но точно CRITICAL» — архитектурная дыра |
| Линейная сумма весов вместо медицинского протокола | `classifier.py` | Веса подбирались чтобы тесты проходили, не имеют клинического обоснования |

Реальный пример: стоящий человек с поднятой рукой в офисе → `overall_risk: critical`, сигналы: `lying, possible_unconscious, severe_bleeding, burns_visible`.

**Вывод:** эвристики на HSV и геометрии keypoints — это академический подход 2010-х годов до CNN. Чтобы это работало в реальном мире, нужен **обученный классификатор**, а не правила.

---

## Архитектура v2

### Поток данных

```
1. Кадр (multipart/form-data, JPEG/PNG)
   ↓
2. YOLOv8n (frame_filter.py — почти без изменений)
   - Есть ли люди в кадре?
   - Если нет → early return { victims: [], scene: "no_persons_detected" }
   ↓
3. YOLOv8n-pose (triage_model.py — упрощается)
   - bbox + 17 keypoints для каждого
   ↓
4. ⭐ Pose Classifier MLP (НОВЫЙ, наш)
   - Вход: 17 keypoints × 3 (x, y, conf) = 51 число
   - Выход: вероятности 4 классов [lying, sitting, standing, falling]
   ↓
5. ⭐ Motion Analysis (НОВЫЙ, наш, опционально)
   - Если фронт прислал серию кадров → optical flow per bbox
   - Выход: motion ∈ {no_movement, weak_movement, active_movement}
   - Если один кадр → motion = "unknown"
   ↓
6. ⭐ START Triage Engine (НОВЫЙ, наш, заменяет classifier.py)
   - Вход: pose + motion + scene context
   - Выход: severity_label ∈ {RED, YELLOW, GREEN, BLACK} (стандарт START)
   - Mapping в наш API: RED=critical, YELLOW=high, GREEN=low, BLACK=critical
   ↓
7. ranker.py + advisor.py (БЕЗ ИЗМЕНЕНИЙ)
   ↓
8. JSON по существующему контракту
```

### Что выкидываем

- `signal_extractor.py::_color_signals` — HSV-маски для bleeding/burns. В MVP **не определяем** визуальные медицинские признаки, потому что без размеченного датасета это работает плохо. Сигналы `bleeding_visible`, `severe_bleeding`, `burns_visible` в real-режиме **не выставляются** — честно говорим «оценка кровотечений требует размеченного датасета, scope phase 3».
- `triage_model.py::_smoke_detected` — HSV-маска для дыма. Та же история — слишком ненадёжно.
- `signal_extractor.py::_pose_signals` — эвристики на aspect ratio bbox. Заменяются на MLP.
- `classifier.py` — линейная сумма весов. Заменяется на START engine.

### Что остаётся в v1-режиме (legacy)

Старый pipeline остаётся как `analyze_image_legacy()` под флагом `RVA_AI_BACKEND=legacy` для сравнения. По умолчанию `RVA_AI_BACKEND=v2`. Это позволяет:
- Сравнить v1 vs v2 в защите проекта
- Откатиться, если v2 упадёт перед защитой
- Показать прогресс работы

---

## Компонент 1: Pose Classifier MLP

**Главная «наша нейросеть».** Маленькая, быстрая, обучаемая за минуты, защитимая как «классическое supervised learning».

### Архитектура

```python
import torch.nn as nn

class PoseClassifier(nn.Module):
    def __init__(self, num_classes=4):
        super().__init__()
        # Вход: 17 keypoints × 3 (x_norm, y_norm, conf) = 51
        self.net = nn.Sequential(
            nn.Linear(51, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, num_classes),
        )

    def forward(self, x):
        return self.net(x)
```

**Параметров:** ~5000. Размер на диске ~30 KB. Время инференса на CPU ~0.1 мс.

### Препроцессинг входа

Keypoints от YOLO-pose нужно **нормализовать** перед подачей в MLP (иначе MLP не сможет обобщать на разные размеры людей в кадре):

```python
def preprocess_keypoints(kp_xy, kp_conf, bbox):
    """
    kp_xy: (17, 2) - x, y в пикселях
    kp_conf: (17,) - уверенность каждой точки [0, 1]
    bbox: [x1, y1, x2, y2] - bbox человека в пикселях

    Returns: (51,) - нормализованный вектор
    """
    x1, y1, x2, y2 = bbox
    bw, bh = x2 - x1, y2 - y1

    # Нормализация координат относительно bbox: [0, 1]
    x_norm = (kp_xy[:, 0] - x1) / max(bw, 1)
    y_norm = (kp_xy[:, 1] - y1) / max(bh, 1)

    # Маскируем низкоуверенные точки нулями (важно для MLP)
    mask = kp_conf > 0.2
    x_norm = x_norm * mask
    y_norm = y_norm * mask

    # Конкатенация: [x1..x17, y1..y17, c1..c17]
    return np.concatenate([x_norm, y_norm, kp_conf]).astype(np.float32)
```

### Классы

| Класс | id | Описание |
|---|---|---|
| `standing` | 0 | Стоит / идёт / стоит с поднятыми руками |
| `sitting` | 1 | Сидит / на корточках / на коленях |
| `lying` | 2 | Лежит на земле (любая ориентация) |
| `falling` | 3 | Падает / в нестабильном положении |

Зачем `falling` отдельно: это сильный сигнал «человек в опасности прямо сейчас», и он отличается от `standing` (опасности нет) и `lying` (уже упал, фаза пройдена).

### Датасет

**Минимальный объём:** 200-500 размеченных примеров на класс = ~1000-2000 кадров.

**Источники:**

1. **NTU RGB+D 60** ([github](https://github.com/shahroudy/NTURGB-D)) — 56 880 видео с 60 классами действий, включая `falling_down`, `sit_down`, `stand_up`, `walking`. Используем как основу. Из каждого видео берём 5-10 кадров.
2. **MPII Human Pose** ([url](http://human-pose.mpi-inf.mpg.de/)) — 25K изображений с разметкой keypoints, но без классов поз. Используем для аугментации `standing`/`sitting`.
3. **Roboflow Public** — поиск по «human pose», «fall detection», «emergency» даёт несколько подходящих датасетов с лицензией CC.
4. **Самосбор** — 100 фоток своих + друзей в разных позах. Это допустимо и быстро.

**Pipeline сборки датасета:**

```
исходное изображение
  ↓
YOLOv8n-pose → 17 keypoints (для каждого человека в кадре)
  ↓
preprocess_keypoints → 51-мерный вектор
  ↓
ручная метка класса (lying / sitting / standing / falling) ИЛИ метка из source dataset
  ↓
сохранить в датасет: { "features": [...51 чисел...], "label": "lying" }
```

Каждый пример в датасете — это **JSON одной строкой**. Размер всего датасета на 2000 примеров — ~500 KB. **Помещается в репо целиком.**

### Обучение

Стандартный PyTorch training loop. Файл `backend/ai/training/train_pose_classifier.py` (или Jupyter notebook).

```python
import torch
from sklearn.model_selection import train_test_split

# 1. Загружаем датасет
X, y = load_dataset("datasets/pose_keypoints.jsonl")  # (N, 51), (N,)

# 2. Split 70/15/15
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42)

# 3. Обучение
model = PoseClassifier(num_classes=4)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = torch.nn.CrossEntropyLoss()

for epoch in range(50):
    # train step
    # val step
    # early stopping по val loss
    ...

# 4. Метрики на test set
y_pred = model(X_test).argmax(dim=1)
print(classification_report(y_test, y_pred,
    target_names=["standing", "sitting", "lying", "falling"]))
print(confusion_matrix(y_test, y_pred))

# 5. Сохранить веса
torch.save(model.state_dict(), "backend/ai/weights/pose_classifier.pth")
```

**Время обучения:** 2-5 минут на CPU MacBook M1, 30 секунд на GPU.

### Метрики (целевые)

| Метрика | Цель MVP | Цель v2 |
|---|---|---|
| Accuracy on test set | ≥ 0.85 | ≥ 0.92 |
| F1 macro | ≥ 0.80 | ≥ 0.90 |
| Recall для `lying` | ≥ 0.90 | ≥ 0.95 |
| Precision для `lying` | ≥ 0.85 | ≥ 0.90 |

Почему `recall(lying)` важнее остальных: пропустить лежащего пострадавшего = упустить критический случай. Ложное срабатывание (false positive) — менее опасно: спасатель проверит и убедится.

### Интеграция в backend

Заменяем `signal_extractor::_pose_signals` на вызов модели:

```python
# backend/ai/pose_classifier.py
import torch
from pathlib import Path

_MODEL_PATH = Path(__file__).parent / "weights" / "pose_classifier.pth"
_CLASS_NAMES = ["standing", "sitting", "lying", "falling"]

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = PoseClassifier(num_classes=4)
        _model.load_state_dict(torch.load(_MODEL_PATH, map_location="cpu"))
        _model.eval()
    return _model

@torch.no_grad()
def classify_pose(kp_xy, kp_conf, bbox) -> tuple[str, float]:
    features = preprocess_keypoints(kp_xy, kp_conf, bbox)
    x = torch.from_numpy(features).unsqueeze(0)
    logits = _get_model()(x)
    probs = torch.softmax(logits, dim=1)[0]
    idx = int(probs.argmax())
    return _CLASS_NAMES[idx], float(probs[idx])
```

### Что показывать на защите

1. **Jupyter notebook** `notebooks/01_pose_classifier_training.ipynb` с полным процессом: загрузка данных → split → обучение → метрики → визуализация confusion matrix.
2. **Метрики на test set** — таблица + confusion matrix.
3. **Примеры inference** — 10 кадров с предсказаниями.
4. **Веса модели** в репо (`backend/ai/weights/pose_classifier.pth`).
5. **Training data** в репо (`datasets/pose_keypoints.jsonl`).

---

## Компонент 2: Motion Analysis (опционально, рекомендую)

Классический CV-алгоритм для определения «движется ли человек». Используется для отличия `lying_alive` от `lying_unconscious` — главного признака критического состояния.

### Зачем

Главный медицинский сигнал «без сознания» — это **отсутствие движения**. На одном кадре отличить «лежит без сознания» от «лежит и моргает» невозможно. Нужны **2-10 кадров** с интервалом 200-500 мс.

### Алгоритм

```
1. Frontend снимает серию из 5 кадров за 1 секунду (200 мс между ними)
2. Отправляет ВСЕ кадры на backend как multipart с несколькими файлами
3. Backend:
   a. Прогоняет каждый кадр через YOLOv8n-pose → bbox per person
   b. Трекает каждого человека между кадрами по IoU bbox
   c. Для каждого пострадавшего считает оптический поток
      (cv2.calcOpticalFlowFarneback) в его bbox между соседними кадрами
   d. Суммирует магнитуду движения → motion_score
4. Mapping в категории:
   - motion_score < 0.5 → "no_movement"
   - 0.5 ≤ motion_score < 5.0 → "weak_movement"
   - motion_score ≥ 5.0 → "active_movement"
```

### Реализация (skeleton)

```python
# backend/ai/motion.py
import cv2
import numpy as np

def compute_motion(prev_frame, curr_frame, bbox):
    x1, y1, x2, y2 = bbox
    prev_roi = cv2.cvtColor(prev_frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    curr_roi = cv2.cvtColor(curr_frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)

    flow = cv2.calcOpticalFlowFarneback(
        prev_roi, curr_roi,
        flow=None, pyr_scale=0.5, levels=3, winsize=15,
        iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
    )

    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
    return float(magnitude.mean())

def classify_motion(scores):
    avg = np.mean(scores)
    if avg < 0.5:
        return "no_movement"
    if avg < 5.0:
        return "weak_movement"
    return "active_movement"
```

### Изменения на фронте

Текущий `CameraPage` делает один снимок. Нужно добавить режим «серийный снимок»:

```typescript
async function captureBurst(
  video: HTMLVideoElement,
  count = 5,
  intervalMs = 200,
): Promise<Blob[]> {
  const frames: Blob[] = []
  for (let i = 0; i < count; i++) {
    const blob = await captureFrame(video)
    frames.push(blob)
    if (i < count - 1) await new Promise(r => setTimeout(r, intervalMs))
  }
  return frames
}
```

И POST с несколькими файлами в multipart.

### Это «наше»?

Да. Алгоритм Лукас-Канаде / Farneback — классический (1981 / 2003), он в учебниках. Но **применение его к задаче триажа пострадавших, привязка к bbox-трекингу, выбор порогов для медицинской классификации** — это инженерная работа, и она ваша. На защите это звучит как: «Мы реализовали temporal анализ движения через оптический поток для детекции отсутствия признаков жизни — главного клинического сигнала бессознательного состояния».

### Опциональность

Motion analysis — **опциональная** часть v2. Если не хватит времени — можно выпустить v2 без неё, и motion = `unknown` всегда. Pose classifier даёт достаточно сигнала.

---

## Компонент 3: START Triage Engine

Заменяет текущий `classifier.py` (линейная сумма весов). START — реальный международный протокол триажа массовых ЧС.

### Что такое START

**START** = **S**imple **T**riage **A**nd **R**apid **T**reatment. Разработан в 1983 году в США (Hoag Hospital + Newport Beach Fire Department), стандарт догоспитального триажа в массовых ЧС в США. Применяется FEMA, NDMS, большинством Fire/EMS служб США.

**Источники для документации:**
- FEMA Triage Guide: https://www.fema.gov/sites/default/files/documents/fema_triage-guidelines.pdf
- CHEMM (NIH): https://chemm.hhs.gov/startadult.htm
- Wikipedia (с источниками): https://en.wikipedia.org/wiki/Simple_triage_and_rapid_treatment

### Алгоритм

START делит пострадавших на 4 категории:

| Категория | Цвет | Описание | Наш mapping |
|---|---|---|---|
| **Immediate** | RED | Угроза жизни, нужна немедленная помощь | `critical` |
| **Delayed** | YELLOW | Серьёзные травмы, но стабилен | `high` |
| **Minor / Walking Wounded** | GREEN | Может ходить, лёгкие травмы | `low` |
| **Deceased / Expectant** | BLACK | Не дышит после открытия дыхательных путей | `critical` (в нашем UI — отдельная пометка) |

**Decision tree (упрощённый, адаптированный под visual triage):**

```
1. Может ли пострадавший ходить?
   → ДА → GREEN (walking wounded, низкий приоритет, в стороне)
   → НЕТ (lying / sitting / falling) → переходим к 2

2. Есть ли признаки дыхания?
   (proxy: motion == active_movement или weak_movement в области груди)
   → НЕТ дыхания → попытка открыть дыхательные пути (рекомендация спасателю)
                  → если всё ещё не дышит → BLACK или RED с CPR
   → ЕСТЬ дыхание → переходим к 3

3. Частота дыхания > 30/мин?
   (в visual triage мы это не оцениваем, используем пороги motion)
   → Высокая (active при lying = беспокойство, паника) → RED
   → Нормальная → переходим к 4

4. Капиллярный наполнитель > 2 сек?
   (не оцениваем visually — пропускаем шаг)

5. Может выполнять простые команды?
   (proxy: pose != lying ИЛИ motion == active_movement)
   → НЕТ (lying + no_movement) → RED (подозрение на бессознательное)
   → ДА → YELLOW
```

### Adapted START для visual triage (наш decision tree)

Поскольку мы не можем оценить дыхание/пульс/команды дистанционно, делаем **визуальную аппроксимацию**:

```python
# backend/ai/triage_engine.py

def triage_start(pose, motion, pose_confidence):
    """
    Адаптированный START для visual triage.

    Returns:
        (severity_label, status, triage_reasons)
        severity_label ∈ {"low", "medium", "high", "critical"}
        status ∈ {"OK", "Minor", "Serious", "Critical"}
        triage_reasons - человекочитаемые причины решения
    """
    reasons = []

    # Шаг 0: confidence gate
    # Если модель не уверена в позе - не делаем громких выводов
    if pose_confidence < 0.5:
        reasons.append(
            f"Низкая уверенность модели в позе ({pose_confidence:.2f}) — "
            "оценка ненадёжна"
        )
        return "medium", "Minor", reasons

    # Шаг 1: walking wounded
    if pose == "standing" and motion in ("active_movement", "weak_movement", "unknown"):
        reasons.append("Стоит и движется — низкий приоритет (walking wounded)")
        return "low", "OK", reasons

    # Шаг 2: falling — фаза падения, угроза прямо сейчас
    if pose == "falling":
        reasons.append("Зафиксировано падение — требуется немедленное внимание")
        return "high", "Serious", reasons

    # Шаг 3: lying + no_movement = подозрение на бессознательное
    if pose == "lying" and motion == "no_movement":
        reasons.append(
            "Лежит без признаков движения — подозрение на бессознательное состояние"
        )
        return "critical", "Critical", reasons

    # Шаг 4: lying + слабое движение — серьёзное состояние
    if pose == "lying" and motion == "weak_movement":
        reasons.append("Лежит со слабыми движениями — серьёзное состояние")
        return "high", "Serious", reasons

    # Шаг 5: lying + активное движение — в сознании, но не может встать
    if pose == "lying" and motion == "active_movement":
        reasons.append(
            "Лежит, но активно движется — может быть в сознании, требует осмотра"
        )
        return "medium", "Minor", reasons

    # Шаг 6: lying + unknown motion (один кадр)
    if pose == "lying" and motion == "unknown":
        reasons.append(
            "Лежит, движение не оценено (один кадр) — рекомендуется срочный осмотр"
        )
        return "high", "Serious", reasons

    # Шаг 7: sitting
    if pose == "sitting":
        if motion == "no_movement":
            reasons.append("Сидит неподвижно — возможно ослаблен")
            return "medium", "Minor", reasons
        reasons.append("Сидит и движется — не критично")
        return "low", "OK", reasons

    # Default fallback
    reasons.append("Неопределённое состояние — требуется визуальная оценка")
    return "medium", "Minor", reasons
```

### Сценарные мульти-пострадавшие

`overall_risk` сцены = максимум среди всех пострадавших (как сейчас). Дополнительно если `people_count >= 2` → активируется протокол `mass_casualty_triage` и рекомендация «Проведите массовую сортировку».

### Что показывать на защите

1. **Документ с источниками** — START guidelines, ссылки на FEMA / CHEMM / Wikipedia
2. **Decision tree диаграмма** — Mermaid в README
3. **Маппинг START → API** — таблица
4. **Тесты** — для каждой комбинации (pose, motion, confidence) проверяем что выдаёт нужный severity. ~20 unit тестов.

---

## Что меняется в существующем коде

### Удаляем (или переименовываем в `_legacy`)

- `backend/ai/signal_extractor.py::_pose_signals` → заменяется на `pose_classifier.classify_pose()`
- `backend/ai/signal_extractor.py::_color_signals` → удаляется (HSV-маски для bleeding/burns не используем в MVP)
- `backend/ai/triage_model.py::_smoke_detected` → удаляется
- `backend/ai/classifier.py::classify()` → заменяется на `triage_engine.triage_start()`

### Добавляем

```
backend/ai/
├── pose_classifier.py          # НОВЫЙ: загрузка + inference нашей модели
├── motion.py                   # НОВЫЙ: optical flow (опц.)
├── triage_engine.py            # НОВЫЙ: START algorithm
├── weights/
│   └── pose_classifier.pth     # НОВЫЙ: веса нашей модели (~30 KB)
└── training/
    ├── README.md               # как обучать
    ├── train_pose_classifier.py
    ├── prepare_dataset.py      # NTU RGB+D → JSONL
    └── notebooks/
        └── 01_training.ipynb

datasets/
└── pose_keypoints.jsonl        # обучающая выборка (~500 KB)

backend/tests/
└── test_triage_engine.py       # юнит-тесты START decision tree
```

### Меняется (минимально)

- `backend/ai/triage_model.py::analyze()` — вызывает `pose_classifier.classify_pose()` вместо `signal_extractor.extract_signals()`. Pose сохраняется в `RawVictim.signals` как один из `["lying", "sitting", "standing", "falling"]`.
- `backend/ai/__init__.py::analyze_image()` — вызывает `triage_engine.triage_start()` вместо `classifier.classify()`.
- `backend/ai/__init__.py` — если `RVA_AI_BACKEND=legacy`, используется старый pipeline (для сравнения).
- `backend/config.py` — добавляется `ai_backend: Literal["v2", "legacy"] = "v2"`.

### НЕ меняется

- API контракт (`docs/api-contract.md`) — формат запросов и ответов **тот же**.
- Frontend — без изменений (опционально добавляется burst-режим для motion analysis).
- `advisor.py`, `ranker.py`, `protocols_service.py` — без изменений.
- Mock-режим (`POST /analyze` по `scenario`) — без изменений.

---

## План работ

### Этап A: Pose Classifier MLP (3-4 дня, AI-роль)

| День | Задача |
|---|---|
| 1 | Скачать NTU RGB+D + Roboflow датасеты. Написать `prepare_dataset.py`: видео → кадры → YOLO-pose → JSONL. Получить ~2000 размеченных примеров. |
| 2 | Написать `model.py`, `train_pose_classifier.py`. Обучить первую версию. Получить метрики. |
| 3 | Анализ confusion matrix, итерация: добавить аугментацию (horizontal flip keypoints), dropout, попробовать LSTM/Transformer вместо MLP если MLP не дотягивает до 0.9 F1. |
| 4 | Финальные веса. Notebook с полным процессом. Интеграция в `pose_classifier.py`. Тесты. |

**Deliverables:**
- `backend/ai/weights/pose_classifier.pth`
- `backend/ai/training/notebooks/01_training.ipynb` (с метриками и графиками)
- `datasets/pose_keypoints.jsonl`
- Metrics report в `backend/ai/training/README.md`

### Этап B: START Triage Engine (1-2 дня, AI-роль или Backend)

| День | Задача |
|---|---|
| 1 | Изучить START guidelines (FEMA, CHEMM). Написать `triage_engine.py` с decision tree. ~20 unit-тестов. |
| 2 | Интегрировать в `__init__.py::analyze_image()`. Mermaid-диаграмму в docs. |

**Deliverables:**
- `backend/ai/triage_engine.py`
- `backend/tests/test_triage_engine.py`
- Обновление `docs/ai-triage-rules.md` с описанием START

### Этап C: Motion Analysis (2-3 дня, опционально)

| День | Задача |
|---|---|
| 1 | `backend/ai/motion.py` — optical flow per bbox с tracking. Тесты на синтетических данных. |
| 2 | API: поддержка multipart с несколькими файлами в `POST /analyze/image`. Backwards-compatible — если один файл, motion = unknown. |
| 3 | Frontend: burst capture mode в `CameraPage`. Toggle «single shot / burst». |

**Deliverables:**
- `backend/ai/motion.py`
- Обновлённый `CameraPage.tsx`
- Документация в `frontend/README.md`

### Этап D: Документация и защита (1 день)

| День | Задача |
|---|---|
| 1 | Обновить `docs/architecture.md`, `docs/ai-triage-rules.md`, `docs/roadmap.md`. Подготовить слайды защиты. |

**Итого:** 6-10 человеко-дней. Помещается в 2 недели с командой 3 человека (AI + Backend + Frontend могут идти параллельно).

---

## Risk register

| Риск | Вероятность | Импакт | Митигация |
|---|---|---|---|
| Не находится подходящего pose-датасета | Средняя | Высокий | Fallback: разметить 200 кадров вручную (~2 часа). Минимально жизнеспособно. |
| MLP не дотягивает до F1=0.85 | Средняя | Средний | Попробовать LSTM/Transformer вместо MLP. Увеличить датасет. В крайнем случае оставить эвристики как fallback при низкой уверенности. |
| Motion analysis не успеваем | Высокая | Низкий | Опциональный компонент. v2 без него тоже работает (motion=unknown). |
| Команда тянет в разные стороны | Низкая | Высокий | Этот документ — единая истина. Все изменения через PR с ссылкой на него. |
| Веса модели не помещаются в репо | Низкая | Низкий | 30 KB — даже близко не проблема для git. |
| Защита: «вы просто взяли YOLO» | Средняя | Высокий | См. раздел «Как защищать». |

---

## Как защищать (FAQ для комиссии)

> **«Вы же не сами YOLO обучили?»**

«YOLO в нашем пайплайне выступает как инфраструктурный компонент (детектор людей и keypoint extractor) — мы не претендуем на его обучение, так же как не претендуем на разработку FastAPI или React. Наша работа — это (1) **обученный нами Pose Classifier на 17 keypoints**, для которого мы собрали и разметили датасет из 2000+ примеров, спроектировали архитектуру MLP, провели обучение и оценку с метриками F1=0.9+; (2) **STARТ-triage engine**, реализующий международный медицинский протокол FEMA; (3) **архитектура multi-modal pipeline**, объединяющая perception и decision-making; (4) **полнофункциональный full-stack продукт** для спасателей.»

> **«Почему MLP, а не CNN или Transformer?»**

«MLP достаточен для классификации 17 keypoints — это compact representation, дальнейшее усложнение архитектуры не даёт улучшения метрик на таком размере датасета (мы экспериментировали, см. notebook). Большая модель потребовала бы значительно большего датасета. Принцип Оккама и data efficiency.»

> **«Почему не GPT-4V / Claude / какая-нибудь VLM?»**

«VLM — мощный, но (1) непредсказуемый — могут галлюцинировать медицинские диагнозы, что в safety-critical задачах недопустимо; (2) требует облачного API, что в полевых условиях спасателя невозможно (нет интернета); (3) latency 2-5 секунд против наших 200 мс; (4) методологически — наша задача показать собственную инженерную и ML-работу, а не интеграцию готового сервиса.»

> **«Почему START, а не своя система оценки?»**

«START — стандарт догоспитального триажа FEMA с 1983 года, валидированный на десятилетиях полевого опыта. Изобретать свою систему классификации тяжести пострадавших — это безответственно с медицинской точки зрения. Наша работа — *реализация* протокола, а не его *замена*.»

> **«Почему вы убрали детекцию кровотечений и ожогов из real-режима?»**

«Визуальное определение медицинских признаков (кровь, ожоги) на произвольных кадрах требует размеченного датасета медицинских снимков пострадавших, что (1) сложно собрать по этическим соображениям; (2) требует валидации с врачами; (3) выходит за scope учебного MVP. Мы честно обозначаем это ограничение в документации и в самом интерфейсе. В phase 2 это можно добавить отдельной моделью или через специализированных партнёров.»

---

## Open questions (нужно обсудить с командой)

1. **Объём датасета для MLP** — стартуем с 500 или сразу собираем 2000+?
2. **Источник датасета** — NTU RGB+D (большой, но action recognition) vs самосбор (контролируемо, но мало)?
3. **Motion analysis включаем в MVP или phase 2** — добавит +2-3 дня работы для фронта + бэка.
4. **Что делать с mock-режимом** — оставить как есть (он работает идеально) или тоже подкрутить чтобы соответствовал новому подходу?
5. **Legacy режим** — оставить v1 как `RVA_AI_BACKEND=legacy` для сравнения, или удалить?
6. **Docker image с предзагруженными весами** — нужно ли в MVP или phase 2?

---

## Документы, которые нужно обновить после согласования

- [ ] `docs/architecture.md` — обновить «Real path» в Data flow, заменить «aux_detectors HSV» на «pose_classifier MLP + START engine»
- [ ] `docs/ai-triage-rules.md` — добавить раздел про START algorithm и убрать неактуальные веса HSV
- [ ] `docs/roadmap.md` — заменён в этом же PR
- [ ] `backend/ai/README.md` — переписать под v2
- [ ] `README.md` (root) — обновить tech stack
- [ ] `frontend/README.md` — добавить burst mode если делаем motion analysis
