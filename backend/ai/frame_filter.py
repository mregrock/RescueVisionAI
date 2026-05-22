from dataclasses import dataclass, field

import cv2
import numpy as np

_PERSON_CLASS_ID = 0
_CONF_THRESHOLD = 0.30
_BRIGHTNESS_THRESHOLD = 30
_MODEL_NAME = "yolov8n.pt"

_model = None


def _get_model():
    global _model
    if _model is None:
        from ultralytics import YOLO  # noqa: PLC0415

        _model = YOLO(_MODEL_NAME)
    return _model


@dataclass
class FilterResult:
    is_relevant: bool
    person_boxes: list[list[int]] = field(default_factory=list)
    low_visibility: bool = False
    reason: str | None = None


def filter_frame(image_bytes: bytes) -> FilterResult:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return FilterResult(is_relevant=False, reason="cannot_decode_image")

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    low_vis = float(gray.mean()) < _BRIGHTNESS_THRESHOLD

    results = _get_model()(bgr, verbose=False, conf=_CONF_THRESHOLD, classes=[_PERSON_CLASS_ID])

    boxes: list[list[int]] = []
    for result in results:
        if result.boxes is None:
            continue
        for box in result.boxes:
            if int(box.cls[0]) == _PERSON_CLASS_ID:
                boxes.append([int(v) for v in box.xyxy[0].tolist()])

    if not boxes:
        reason = "low_visibility_no_persons" if low_vis else "no_persons_detected"
        return FilterResult(is_relevant=False, low_visibility=low_vis, reason=reason)

    return FilterResult(is_relevant=True, person_boxes=boxes, low_visibility=low_vis)
