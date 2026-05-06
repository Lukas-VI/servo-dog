from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

from ..config import RuntimeConfig
from ..models import VisionResult


@dataclass
class VisionDebug:
    enabled: bool = False
    out_dir: Optional[Path] = None
    every_n: int = 10


class PureVisionTracker:
    def __init__(self, cfg: RuntimeConfig, debug: Optional[VisionDebug] = None) -> None:
        self.cfg = cfg
        self.debug = debug or VisionDebug()
        self._frame_index = 0

    def process(self, frame) -> VisionResult:
        import cv2

        self._frame_index += 1
        resized = cv2.resize(frame, (self.cfg.frame_width, self.cfg.frame_height))
        roi = resized[int(self.cfg.frame_height * 0.36) :, :]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        adaptive = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            21,
            5,
        )
        edges = cv2.Canny(adaptive, 80, 180)
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=18,
            minLineLength=max(16, self.cfg.frame_width // 12),
            maxLineGap=12,
        )

        error, angle, confidence = self._line_model(lines, edges.shape)
        detected_colors = self._detect_colors(resized)
        debug_frame = self._draw_debug(resized, roi, lines, error, confidence)
        self._maybe_write_debug(debug_frame)
        return VisionResult(
            line_error=error,
            line_angle=angle,
            confidence=confidence,
            detected_colors=detected_colors,
            debug_frame=debug_frame,
        )

    def _line_model(self, lines, shape: Tuple[int, int]) -> Tuple[float, float, float]:
        height, width = shape
        if lines is None or len(lines) == 0:
            return 0.0, 0.0, 0.0

        weighted_x = 0.0
        weighted_angle = 0.0
        total_weight = 0.0
        for item in lines[:, 0, :]:
            x1, y1, x2, y2 = [float(v) for v in item]
            length = float(np.hypot(x2 - x1, y2 - y1))
            if length < 8:
                continue
            bottom_weight = 1.0 + max(y1, y2) / max(height, 1)
            weight = length * bottom_weight
            weighted_x += ((x1 + x2) * 0.5) * weight
            weighted_angle += float(np.arctan2(y2 - y1, x2 - x1)) * weight
            total_weight += weight
        if total_weight <= 0:
            return 0.0, 0.0, 0.0

        center_x = weighted_x / total_weight
        error = (center_x - width * 0.5) / (width * 0.5)
        error = max(-1.0, min(1.0, error))
        angle = weighted_angle / total_weight
        confidence = max(0.0, min(1.0, total_weight / (width * height * 0.18)))
        return error, angle, confidence

    def _detect_colors(self, frame) -> Dict[str, float]:
        import cv2

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        scores: Dict[str, float] = {}
        pixels = float(frame.shape[0] * frame.shape[1])
        for name, (lower, upper) in self.cfg.colors_hsv.items():
            if name == "black":
                continue
            mask = cv2.inRange(hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
            scores[name] = float(cv2.countNonZero(mask)) / pixels
        return scores

    def _draw_debug(self, resized, roi, lines, error: float, confidence: float):
        import cv2

        debug = resized.copy()
        offset_y = resized.shape[0] - roi.shape[0]
        if lines is not None:
            for x1, y1, x2, y2 in lines[:, 0, :]:
                cv2.line(debug, (x1, y1 + offset_y), (x2, y2 + offset_y), (40, 220, 255), 1)
        center = resized.shape[1] // 2
        target = int(center + error * center)
        cv2.line(debug, (center, 0), (center, resized.shape[0]), (255, 255, 255), 1)
        cv2.line(debug, (target, 0), (target, resized.shape[0]), (0, 80, 255), 2)
        cv2.putText(
            debug,
            f"err={error:+.2f} conf={confidence:.2f}",
            (8, 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        return debug

    def _maybe_write_debug(self, frame) -> None:
        if not self.debug.enabled or self.debug.out_dir is None:
            return
        if self._frame_index % self.debug.every_n != 0:
            return
        import cv2

        self.debug.out_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(self.debug.out_dir / f"frame_{self._frame_index:06d}.jpg"), frame)
