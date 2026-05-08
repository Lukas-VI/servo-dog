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
        self._last_center_error = 0.0
        self._last_confidence = 0.0

    def process(self, frame) -> VisionResult:
        import cv2

        self._frame_index += 1
        resized = cv2.resize(frame, (self.cfg.frame_width, self.cfg.frame_height))
        roi_start = int(self.cfg.frame_height * float(getattr(self.cfg.vision, "roi_start_ratio", 0.48)))
        roi_start = max(0, min(self.cfg.frame_height - 2, roi_start))
        roi = resized[roi_start:, :]

        mask = self._track_mask(roi)
        edges = cv2.Canny(mask, 70, 160)
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=14,
            minLineLength=max(14, self.cfg.frame_width // 14),
            maxLineGap=10,
        )

        line_error, line_angle, line_confidence = self._line_model(lines, edges.shape)
        stripe_error, stripe_angle, stripe_confidence = self._stripe_model(mask)
        if stripe_confidence > 0.0:
            smooth = max(0.0, min(0.9, float(getattr(self.cfg.vision, "temporal_smoothing", 0.35))))
            error = stripe_error * (1.0 - smooth) + self._last_center_error * smooth
            angle = stripe_angle
            confidence = max(stripe_confidence, line_confidence * 0.7)
        else:
            error, angle, confidence = line_error, line_angle, line_confidence
        if confidence > 0.05:
            self._last_center_error = error
            self._last_confidence = confidence
        branches, branch_confidence, branch_offsets = self._branch_model(mask)
        detected_colors = self._detect_colors(resized)
        debug_frame = self._draw_debug(resized, roi_start, lines, mask, error, confidence, branches, branch_confidence)
        self._maybe_write_debug(debug_frame)
        return VisionResult(
            line_error=error,
            line_angle=angle,
            confidence=confidence,
            branches=branches,
            branch_confidence=branch_confidence,
            branch_offsets=branch_offsets,
            detected_colors=detected_colors,
            debug_frame=debug_frame,
        )

    def _track_mask(self, roi):
        import cv2

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        _, dark_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        dark_adaptive = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            31,
            7,
        )
        dark = cv2.bitwise_and(dark_otsu, dark_adaptive)

        _, bright_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        bright_adaptive = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            41,
            -5,
        )
        bright = cv2.bitwise_or(bright_otsu, bright_adaptive)

        kernel = np.ones((3, 3), np.uint8)
        candidates = []
        for mask in (bright, dark):
            if bool(getattr(self.cfg.vision, "exclude_background", True)):
                mask = self._apply_ground_gate(mask)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            mask[: int(mask.shape[0] * 0.16), :] = 0
            mask = self._keep_ground_components(mask)
            candidates.append((self._ground_score(mask), mask))
        return max(candidates, key=lambda item: item[0])[1]

    def _apply_ground_gate(self, mask):
        import cv2

        height, width = mask.shape[:2]
        gate = np.zeros_like(mask)
        polygon = np.array(
            [
                [0, height - 1],
                [width - 1, height - 1],
                [int(width * (0.5 + float(getattr(self.cfg.vision, "gate_top_width_ratio", 0.66)) * 0.5)), int(height * 0.08)],
                [int(width * (0.5 - float(getattr(self.cfg.vision, "gate_top_width_ratio", 0.66)) * 0.5)), int(height * 0.08)],
            ],
            dtype=np.int32,
        )
        bottom_width = float(getattr(self.cfg.vision, "gate_bottom_width_ratio", 0.96))
        polygon[0][0] = int(width * (0.5 - bottom_width * 0.5))
        polygon[1][0] = int(width * (0.5 + bottom_width * 0.5))
        cv2.fillPoly(gate, [polygon], 255)
        return cv2.bitwise_and(mask, gate)

    def _ground_score(self, mask) -> float:
        height, width = mask.shape[:2]
        bottom = mask[int(height * 0.62) :, :]
        center = bottom[:, int(width * 0.22) : int(width * 0.78)]
        stripe_error, _, stripe_conf = self._stripe_model(mask)
        center_bonus = max(0.0, 1.0 - abs(stripe_error)) * 1200.0 * stripe_conf
        return float(np.count_nonzero(bottom)) + float(np.count_nonzero(center)) * 0.7 + center_bonus

    def _stripe_model(self, mask) -> Tuple[float, float, float]:
        height, width = mask.shape[:2]
        min_width = max(5, int(width * float(getattr(self.cfg.vision, "stripe_min_width_ratio", 0.08))))
        max_width = max(min_width + 1, int(width * float(getattr(self.cfg.vision, "stripe_max_width_ratio", 0.82))))
        expected_x = width * (0.5 + self._last_center_error * 0.5)
        points = []
        weights = []
        for y0_ratio, y1_ratio in [(0.28, 0.34), (0.38, 0.44), (0.50, 0.56), (0.62, 0.69), (0.76, 0.86), (0.88, 0.98)]:
            y0 = int(height * y0_ratio)
            y1 = max(y0 + 1, int(height * y1_ratio))
            band = mask[y0:y1, :]
            projection = np.count_nonzero(band, axis=0)
            active = projection > max(1, int((y1 - y0) * 0.22))
            runs = []
            start = None
            for index, is_active in enumerate(active):
                if is_active and start is None:
                    start = index
                elif not is_active and start is not None:
                    if min_width <= index - start <= max_width:
                        runs.append((start, index - 1))
                    start = None
            if start is not None and min_width <= width - start <= max_width:
                runs.append((start, width - 1))
            if not runs:
                continue
            run = min(runs, key=lambda item: abs(((item[0] + item[1]) * 0.5) - expected_x))
            center = (run[0] + run[1]) * 0.5
            run_width = run[1] - run[0] + 1
            y = (y0 + y1) * 0.5
            weight = (0.45 + y / max(height, 1)) * min(1.0, run_width / max(min_width * 2.4, 1))
            points.append((center, y))
            weights.append(weight)
            expected_x = center
        if len(points) < 2:
            return 0.0, 0.0, 0.0
        xs = np.array([p[0] for p in points], dtype=float)
        ys = np.array([p[1] for p in points], dtype=float)
        ws = np.array(weights, dtype=float)
        bottom_center = float(np.average(xs[-min(3, len(xs)) :], weights=ws[-min(3, len(ws)) :]))
        error = (bottom_center - width * 0.5) / (width * 0.5)
        error = max(-1.0, min(1.0, error))
        try:
            fit = np.polyfit(ys, xs, 1, w=ws)
            angle = float(np.arctan2(height, fit[0] * height))
        except Exception:
            angle = 0.0
        coverage = len(points) / 6.0
        continuity = 1.0 - min(1.0, float(np.std(xs) / max(width * 0.35, 1.0)))
        confidence = max(0.0, min(1.0, coverage * 0.65 + continuity * 0.35))
        return error, angle, confidence

    def _keep_ground_components(self, mask):
        import cv2

        seed = np.zeros_like(mask)
        height, width = mask.shape[:2]
        seed[int(height * 0.60) :, int(width * 0.12) : int(width * 0.88)] = mask[
            int(height * 0.60) :, int(width * 0.12) : int(width * 0.88)
        ]
        kernel = np.ones((5, 5), np.uint8)
        seed = cv2.dilate(seed, kernel, iterations=2)
        reachable = cv2.bitwise_and(mask, seed)

        previous_count = -1
        current_count = int(np.count_nonzero(reachable))
        while current_count != previous_count:
            previous_count = current_count
            grown = cv2.dilate(reachable, kernel, iterations=1)
            reachable = cv2.bitwise_and(grown, mask)
            current_count = int(np.count_nonzero(reachable))
        mask = reachable

        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        if count <= 1:
            return mask
        keep = np.zeros_like(mask)
        min_area = max(24, int(width * height * 0.004))
        ground_y = int(height * 0.58)
        edge_margin = max(8, int(width * 0.08))
        center_left = int(width * 0.20)
        center_right = int(width * 0.80)
        for label in range(1, count):
            x, y, w, h, area = stats[label]
            if area < min_area:
                continue
            touches_side_edge = x <= edge_margin or x + w >= width - edge_margin
            overlaps_center = x < center_right and x + w > center_left
            if touches_side_edge and not overlaps_center:
                continue
            touches_ground = y + h >= ground_y
            near_bottom = y + h >= height - 4
            broad_track = w >= width * 0.10 and h >= height * 0.10
            too_far_up = y < height * 0.08 and not near_bottom
            slender_background = h > height * 0.55 and w < width * 0.08
            if too_far_up or slender_background:
                continue
            if touches_ground or near_bottom or broad_track:
                keep[labels == label] = 255
        return keep

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
            angle = float(np.arctan2(y2 - y1, x2 - x1))
            if abs(angle) < 0.28:
                continue
            bottom_weight = 1.0 + max(y1, y2) / max(height, 1)
            weight = length * bottom_weight
            weighted_x += ((x1 + x2) * 0.5) * weight
            weighted_angle += angle * weight
            total_weight += weight
        if total_weight <= 0:
            return 0.0, 0.0, 0.0

        center_x = weighted_x / total_weight
        error = (center_x - width * 0.5) / (width * 0.5)
        error = max(-1.0, min(1.0, error))
        angle = weighted_angle / total_weight
        confidence = max(0.0, min(1.0, total_weight / (width * height * 0.06)))
        return error, angle, confidence

    def _branch_model(self, mask) -> Tuple[Tuple[str, ...], float, Dict[str, float]]:
        height, width = mask.shape[:2]
        far = mask[: max(1, int(height * 0.45)), :]
        far_density = float(np.count_nonzero(far)) / max(float(far.size), 1.0)
        if far_density < 0.035 or far_density > 0.28:
            return (), 0.0, {}
        runs = self._active_column_runs(far)
        if len(runs) < 2:
            return (), 0.0, {}
        offsets: Dict[str, float] = {}
        total_width = 0
        for start, end in runs:
            center = (start + end) * 0.5
            ratio = center / max(width - 1, 1)
            if ratio < 0.40:
                label = "left"
            elif ratio > 0.60:
                label = "right"
            else:
                label = "straight"
            offset = (center - width * 0.5) / (width * 0.5)
            if label not in offsets or abs(offset) < abs(offsets[label]):
                offsets[label] = float(max(-1.0, min(1.0, offset)))
            total_width += end - start + 1
        branches = tuple(label for label in ("left", "straight", "right") if label in offsets)
        if len(branches) < 2:
            return (), 0.0, {}
        confidence = max(0.0, min(1.0, total_width / max(width * 0.45, 1.0)))
        return branches, confidence, offsets

    def _active_column_runs(self, band):
        height, width = band.shape[:2]
        projection = np.count_nonzero(band, axis=0)
        active = projection > max(2, int(height * 0.16))
        runs = []
        start = None
        for index, is_active in enumerate(active):
            if is_active and start is None:
                start = index
            elif not is_active and start is not None:
                if index - start >= max(8, int(width * 0.09)):
                    runs.append((start, index - 1))
                start = None
        if start is not None and width - start >= max(8, int(width * 0.09)):
            runs.append((start, width - 1))
        return runs

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

    def _draw_debug(
        self,
        resized,
        roi_start: int,
        lines,
        mask,
        error: float,
        confidence: float,
        branches: Tuple[str, ...],
        branch_confidence: float,
    ):
        import cv2

        debug = resized.copy()
        offset_y = roi_start
        upper = debug[:offset_y, :].copy()
        shade = np.zeros_like(upper)
        shade[:, :, :] = (28, 28, 28)
        debug[:offset_y, :] = cv2.addWeighted(upper, 0.45, shade, 0.55, 0)
        cv2.line(debug, (0, offset_y), (debug.shape[1] - 1, offset_y), (80, 200, 255), 1)
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        mask_bgr[:, :, 0] = 0
        mask_bgr[:, :, 2] = 0
        debug[offset_y:, :] = cv2.addWeighted(debug[offset_y:, :], 0.74, mask_bgr, 0.34, 0)
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
        if branches:
            cv2.putText(
                debug,
                f"fork={','.join(branches)} {branch_confidence:.2f}",
                (8, 44),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (80, 240, 170),
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
