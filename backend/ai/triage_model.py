import cv2
import numpy as np

from .signal_extractor import extract_signals
from .types import RawScene, RawVictim

_MODEL_NAME = "yolov8n-pose.pt"
_CONF_THRESHOLD = 0.30
_SMOKE_RATIO = 0.35

_model = None


def _get_model():
    global _model
    if _model is None:
        from ultralytics import YOLO  # noqa: PLC0415

        _model = YOLO(_MODEL_NAME)
    return _model


def _smoke_detected(bgr: np.ndarray) -> bool:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 0, 180]), np.array([180, 40, 255]))
    return cv2.countNonZero(mask) / (bgr.shape[0] * bgr.shape[1]) > _SMOKE_RATIO


def _observations(victims: list[RawVictim], scene_signals: list[str]) -> list[str]:
    obs = []
    for v in victims:
        parts = []
        if "lying" in v.signals:
            parts.append("лежит")
        elif "sitting" in v.signals:
            parts.append("сидит")
        else:
            parts.append("стоит")
        if "possible_unconscious" in v.signals:
            parts.append("возможно без сознания")
        if "severe_bleeding" in v.signals:
            parts.append("сильное кровотечение")
        elif "bleeding_visible" in v.signals:
            parts.append("видимое кровотечение")
        if "burns_visible" in v.signals:
            parts.append("ожоги")
        obs.append(f"Пострадавший #{v.local_id}: {', '.join(parts)}")
    if "smoke_or_fire" in scene_signals:
        obs.append("Обнаружены признаки дыма или огня")
    if "low_visibility" in scene_signals:
        obs.append("Низкая видимость — оценка ненадёжна")
    return obs


def analyze(image_bytes: bytes, low_visibility: bool = False) -> tuple[RawScene, list[RawVictim]]:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    results = _get_model()(bgr, verbose=False, conf=_CONF_THRESHOLD)

    victims: list[RawVictim] = []
    pose_confs: list[float] = []

    for result in results:
        if result.boxes is None:
            continue
        kp_data = result.keypoints
        for i, box in enumerate(result.boxes):
            bbox = [int(v) for v in box.xyxy[0].tolist()]
            kp_xy = kp_conf = None
            if kp_data is not None and i < len(kp_data.xy):
                kp_xy = kp_data.xy[i].cpu().numpy()
                kp_conf = kp_data.conf[i].cpu().numpy()

            signals, pc = extract_signals(bgr, bbox, kp_xy, kp_conf)
            pose_confs.append(pc)
            victims.append(RawVictim(local_id=len(victims) + 1, signals=signals, bbox=bbox))

    scene_signals: list[str] = []
    if low_visibility:
        scene_signals.append("low_visibility")
    if len(victims) >= 2:
        scene_signals.append("multiple_victims")
    if _smoke_detected(bgr):
        scene_signals.append("smoke_or_fire")

    base_conf = float(np.mean(pose_confs)) if pose_confs else 0.0
    if low_visibility:
        base_conf = min(base_conf, 0.45)

    scene = RawScene(
        people_count=len(victims),
        observations=_observations(victims, scene_signals),
        scene_signals=scene_signals,
        base_confidence=round(base_conf, 3),
    )
    return scene, victims
