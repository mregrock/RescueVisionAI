import cv2
import numpy as np

_L_SHOULDER, _R_SHOULDER = 5, 6
_L_HIP, _R_HIP = 11, 12
_L_ANKLE, _R_ANKLE = 15, 16

_LYING_ASPECT = 1.3
_SIT_TORSO_RATIO = 0.30
_SIT_ANKLE_RATIO = 0.35
_UNCONSCIOUS_CONF = 0.50
_BLEED_LOW = 0.05
_BLEED_HIGH = 0.15
_BURNS_RATIO = 0.08


def _mid(a: float, b: float) -> float:
    return (a + b) / 2.0


def _pose_signals(
    kp_xy: np.ndarray,
    kp_conf: np.ndarray,
    bbox: list[int],
) -> tuple[list[str], float]:
    x1, y1, x2, y2 = bbox
    bh = max(y2 - y1, 1)
    bw = max(x2 - x1, 1)

    visible = lambda *idx: all(kp_conf[i] > 0.2 for i in idx)  # noqa: E731

    aspect = bw / bh
    if aspect > _LYING_ASPECT:
        pose = "lying"
    elif visible(_L_SHOULDER, _R_SHOULDER, _L_HIP, _R_HIP):
        sh_y = _mid(kp_xy[_L_SHOULDER, 1], kp_xy[_R_SHOULDER, 1])
        hip_y = _mid(kp_xy[_L_HIP, 1], kp_xy[_R_HIP, 1])
        if hip_y - sh_y > _SIT_TORSO_RATIO * bh:
            if visible(_L_ANKLE, _R_ANKLE):
                ank_y = _mid(kp_xy[_L_ANKLE, 1], kp_xy[_R_ANKLE, 1])
                pose = "sitting" if abs(ank_y - hip_y) < _SIT_ANKLE_RATIO * bh else "standing"
            else:
                pose = "standing"
        else:
            pose = "lying"
    else:
        pose = "lying" if aspect > 1.0 else "standing"

    signals = [pose]

    core_conf = float(np.mean([kp_conf[i] for i in (_L_SHOULDER, _R_SHOULDER, _L_HIP, _R_HIP)]))
    if pose == "lying" and core_conf < _UNCONSCIOUS_CONF:
        signals.append("possible_unconscious")

    return signals, core_conf


def _color_signals(bgr: np.ndarray, bbox: list[int]) -> list[str]:
    x1, y1, x2, y2 = bbox
    h, w = bgr.shape[:2]
    y_start = y1 + (y2 - y1) // 3
    roi = bgr[max(0, y_start) : min(h, y2), max(0, x1) : min(w, x2)]
    if roi.size == 0:
        return []

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    total = roi.shape[0] * roi.shape[1]

    red = cv2.bitwise_or(
        cv2.inRange(hsv, np.array([0, 80, 50]), np.array([10, 255, 255])),
        cv2.inRange(hsv, np.array([170, 80, 50]), np.array([180, 255, 255])),
    )
    red_r = cv2.countNonZero(red) / total

    burns = cv2.inRange(hsv, np.array([10, 40, 20]), np.array([30, 200, 100]))
    burns_r = cv2.countNonZero(burns) / total

    signals: list[str] = []
    if red_r >= _BLEED_HIGH:
        signals.append("severe_bleeding")
    elif red_r >= _BLEED_LOW:
        signals.append("bleeding_visible")
    if burns_r >= _BURNS_RATIO:
        signals.append("burns_visible")
    return signals


def extract_signals(
    bgr: np.ndarray,
    bbox: list[int],
    kp_xy: np.ndarray | None = None,
    kp_conf: np.ndarray | None = None,
) -> tuple[list[str], float]:
    if kp_xy is not None and kp_conf is not None:
        pose_sigs, pose_conf = _pose_signals(kp_xy, kp_conf, bbox)
    else:
        x1, y1, x2, y2 = bbox
        aspect = max(x2 - x1, 1) / max(y2 - y1, 1)
        pose_sigs = ["lying"] if aspect > _LYING_ASPECT else ["standing"]
        pose_conf = 0.4

    return pose_sigs + _color_signals(bgr, bbox), pose_conf
