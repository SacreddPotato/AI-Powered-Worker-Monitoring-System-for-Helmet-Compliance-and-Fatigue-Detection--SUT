"""Draw inference annotations onto video frames using OpenCV."""
import cv2

# BGR color palette
_COLORS = {
    'red': (0, 60, 255),
    'green': (0, 200, 80),
    'blue': (255, 160, 50),
    'yellow': (0, 220, 255),
    'cyan': (220, 200, 0),
    'orange': (0, 140, 255),
    'white': (255, 255, 255),
}

_MODEL_COLORS = {
    'helmet': _COLORS['green'],
    'fatigue': _COLORS['orange'],
    'vest': _COLORS['blue'],
    'gloves': _COLORS['yellow'],
    'goggles': _COLORS['cyan'],
    'boots': _COLORS['yellow'],
    'faceshield': _COLORS['cyan'],
    'safetysuit': _COLORS['blue'],
}

_FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_annotations(frame, detections, enabled_overlays=None):
    """Draw detection results onto a frame.

    Args:
        frame: numpy array (BGR)
        detections: dict {model_key: inference_result}
        enabled_overlays: set/list of model keys to draw, or None for all
    Returns:
        Annotated frame (new copy).
    """
    out = frame.copy()
    for model_key, result in detections.items():
        if enabled_overlays and model_key not in enabled_overlays:
            continue
        if result.get('status') != 'ok':
            continue
        payload = result.get('payload', {})
        if model_key == 'fatigue':
            _draw_fatigue(out, payload, model_key)
        else:
            _draw_ppe_boxes(out, payload, model_key)
    return out


def _label_box(frame, text, x1, y1, color):
    (tw, th), _ = cv2.getTextSize(text, _FONT, 0.48, 1)
    cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, text, (x1 + 2, y1 - 3), _FONT, 0.48, (0, 0, 0), 1, cv2.LINE_AA)


# Counting zones use a distinct magenta so they never blend into PPE detection
# boxes (which are green/red/blue/yellow/cyan).
_ZONE_COLOR = (235, 70, 255)  # BGR


def draw_counting_zones(frame, zones):
    """Draw people-counting zones onto ``frame`` (in place) and return it.

    Each zone is always drawn — independent of PPE overlay toggles — so the box
    stays visible at all times, with its current count rendered on the top border.

    Args:
        frame: numpy BGR image (modified in place).
        zones: iterable of dicts with normalized ``x1,y1,x2,y2`` (0..1), ``name``
            and ``count``.
    """
    if not zones:
        return frame

    height, width = frame.shape[:2]
    for zone in zones:
        x1 = max(0, min(width - 1, int(round(float(zone['x1']) * width))))
        y1 = max(0, min(height - 1, int(round(float(zone['y1']) * height))))
        x2 = max(0, min(width - 1, int(round(float(zone['x2']) * width))))
        y2 = max(0, min(height - 1, int(round(float(zone['y2']) * height))))
        if x2 <= x1 or y2 <= y1:
            continue

        cv2.rectangle(frame, (x1, y1), (x2, y2), _ZONE_COLOR, 2)

        label = f"{zone.get('name') or 'Zone'}: {int(zone.get('count', 0))}"
        (tw, th), _ = cv2.getTextSize(label, _FONT, 0.5, 1)
        banner_h = th + 9
        banner_x2 = min(width, x1 + tw + 10)
        if y1 - banner_h >= 0:
            # Banner sits on the top border, above the box.
            cv2.rectangle(frame, (x1, y1 - banner_h), (banner_x2, y1), _ZONE_COLOR, -1)
            text_y = y1 - 5
        else:
            # Box hugs the top of the frame — drop the banner just inside it.
            cv2.rectangle(frame, (x1, y1), (banner_x2, y1 + banner_h), _ZONE_COLOR, -1)
            text_y = y1 + th + 4
        cv2.putText(frame, label, (x1 + 5, text_y), _FONT, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    return frame


def _draw_ppe_boxes(frame, payload, model_key):
    default_color = _MODEL_COLORS.get(model_key, _COLORS['white'])
    for box in payload.get('boxes', []):
        x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
        label = box.get('label', model_key)
        cname = box.get('color', 'green')
        color = _COLORS.get(cname, default_color)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        _label_box(frame, label, x1, y1, color)


def _draw_fatigue(frame, payload, model_key):
    color = _MODEL_COLORS.get(model_key, _COLORS['orange'])
    face_box = payload.get('face_box')
    is_fatigued = payload.get('is_fatigued', False)
    box_color = _COLORS['red'] if is_fatigued else color

    if face_box:
        x1, y1, x2, y2 = face_box['x1'], face_box['y1'], face_box['x2'], face_box['y2']
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        hybrid = payload.get('hybrid_score', 0)
        tag = "FATIGUED" if is_fatigued else "Alert"
        _label_box(frame, f"{tag} ({hybrid:.0%})", x1, y1, box_color)

    # 68-point landmarks
    for pt in payload.get('landmarks', []):
        if len(pt) >= 2:
            cv2.circle(frame, (int(pt[0]), int(pt[1])), 1, color, -1)

    # Head-pose arrow
    pose = payload.get('pose_line')
    if pose:
        cv2.arrowedLine(
            frame,
            tuple(map(int, pose['start'])),
            tuple(map(int, pose['end'])),
            _COLORS['cyan'], 2, tipLength=0.3,
        )

    # Metrics next to face box
    if face_box:
        ear = payload.get('ear')
        mar = payload.get('mar')
        tilt = payload.get('head_tilt_degrees')
        lines = []
        if ear is not None:
            lines.append(f"EAR {ear:.2f}")
        if mar is not None:
            lines.append(f"MAR {mar:.2f}")
        if tilt is not None:
            lines.append(f"Tilt {tilt:.1f}")
        x_t = face_box['x2'] + 5
        y_t = face_box['y1'] + 14
        for i, txt in enumerate(lines):
            cv2.putText(frame, txt, (x_t, y_t + i * 16), _FONT, 0.38, color, 1, cv2.LINE_AA)
