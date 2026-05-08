from __future__ import annotations

import math
from dataclasses import dataclass
from time import monotonic
from typing import Optional

from .config import RuntimeConfig, clamp
from .models import Mode, MotionCommand, VisionResult


COLOR_ACTIONS = {
    "blue": ("updais", Mode.UP_DAIS),
    "brown": ("lean_left", Mode.LEAN_LEFT),
    "purple": ("lean_right", Mode.LEAN_RIGHT),
}


@dataclass
class StateDecision:
    mode: Mode
    motion: Optional[MotionCommand] = None
    action: Optional[str] = None
    reason: str = ""


class EdogStateMachine:
    def __init__(self, cfg: RuntimeConfig, mode: Mode = Mode.STOP) -> None:
        self.cfg = cfg
        self.mode = mode
        self._last_error = 0.0
        self._last_time = monotonic()
        self._action_until = 0.0
        self._map_progress = 0.0
        self._map_edge_index = 0
        self._latched_branch = ""
        self._latched_branch_until = 0.0
        self._last_reliable_error = 0.0
        self._last_reliable_until = 0.0
        self._map_pose = {
            "ok": False,
            "mode": "topology_odometry",
            "message": "task_graph has no usable edge",
        }

    def set_mode(self, mode: Mode) -> None:
        self.mode = mode

    @property
    def map_pose(self) -> dict:
        return dict(self._map_pose)

    def decide(self, vision: VisionResult) -> StateDecision:
        now = monotonic()
        if self.mode == Mode.STOP:
            return StateDecision(Mode.STOP, action="stop", reason="stop mode")
        if now < self._action_until:
            return StateDecision(self.mode, reason="action cooldown")

        if vision.detected_colors:
            for color, score in sorted(
                vision.detected_colors.items(), key=lambda item: item[1], reverse=True
            ):
                if score >= 0.18 and color in COLOR_ACTIONS:
                    action, next_mode = COLOR_ACTIONS[color]
                    self.mode = next_mode
                    self._action_until = now + 1.2
                    return StateDecision(next_mode, action=action, reason=f"color {color}")

        if self.mode in {Mode.TRACK, Mode.BYROAD_A, Mode.BYROAD_B, Mode.LEAN_LEFT, Mode.LEAN_RIGHT, Mode.UP_DAIS}:
            return StateDecision(Mode.TRACK, motion=self._track_motion(vision), reason="vision track")

        return StateDecision(self.mode, action="stop", reason="fallback")

    def _track_motion(self, vision: VisionResult) -> MotionCommand:
        now = monotonic()
        dt = max(now - self._last_time, 1.0 / self.cfg.loop_hz)
        tracking_error = self._select_tracking_error(vision, now)
        min_confidence = float(getattr(self.cfg.pid, "min_track_confidence", 0.18))
        if vision.confidence >= min_confidence:
            self._last_reliable_error = tracking_error
            self._last_reliable_until = now + float(getattr(self.cfg.pid, "lost_rescue_s", 0.45))
        elif now < self._last_reliable_until:
            tracking_error = self._last_reliable_error * float(getattr(self.cfg.pid, "lost_rescue_decay", 0.72))
        derivative = (tracking_error - self._last_error) / dt
        self._last_error = tracking_error
        self._last_time = now

        side = -(self.cfg.pid.kp_side * tracking_error + self.cfg.pid.kd_side * derivative)
        yaw = -(self.cfg.pid.kp_yaw * tracking_error + self.cfg.pid.kd_yaw * derivative)
        if vision.confidence < min_confidence and now >= self._last_reliable_until:
            side = 0.0
            yaw = 0.0
        elif self._target_branch() and vision.branch_confidence >= self.cfg.branch.fork_confidence:
            if self._target_branch() == "left":
                yaw += self.cfg.branch.turn_bias * 0.25
            elif self._target_branch() == "right":
                yaw -= self.cfg.branch.turn_bias * 0.25

        forward = self.cfg.pid.forward_speed if vision.confidence >= min_confidence or now < self._last_reliable_until else 0.03
        if self._target_branch() and (vision.branch_offsets or self._latched_branch):
            forward *= max(0.2, min(1.0, float(self.cfg.branch.fork_speed_factor)))
        motion = MotionCommand(
            forward=forward,
            side=clamp(side, -self.cfg.pid.max_side, self.cfg.pid.max_side),
            yaw=clamp(yaw, -self.cfg.pid.max_yaw, self.cfg.pid.max_yaw),
            stand_height=self.cfg.stand_height,
        )
        self._update_map_pose(vision, motion, dt)
        return motion

    def _target_branch(self) -> str:
        if self.mode == Mode.BYROAD_A:
            return "left"
        if self.mode == Mode.BYROAD_B:
            return "right"
        return str(getattr(self.cfg.branch, "default_turn", "straight") or "straight")

    def _select_tracking_error(self, vision: VisionResult, now: float) -> float:
        target = self._target_branch()
        offsets = vision.branch_offsets or {}
        if target in offsets and vision.branch_confidence >= self.cfg.branch.fork_confidence:
            self._latched_branch = target
            self._latched_branch_until = now + float(self.cfg.branch.branch_latch_s)
            blend = max(0.0, min(1.0, float(self.cfg.branch.branch_error_blend)))
            return vision.line_error * (1.0 - blend) + offsets[target] * blend
        if self._latched_branch == target and now < self._latched_branch_until and target in offsets:
            blend = max(0.0, min(1.0, float(self.cfg.branch.branch_error_blend)))
            return vision.line_error * (1.0 - blend) + offsets[target] * blend
        return vision.line_error

    def _update_map_pose(self, vision: VisionResult, motion: MotionCommand, dt: float) -> None:
        graph = self.cfg.task_graph or {}
        nodes = graph.get("nodes") or []
        edges = graph.get("edges") or []
        if not nodes or not edges:
            self._map_pose = {
                "ok": False,
                "mode": "topology_odometry",
                "message": "task_graph has no usable edge",
            }
            return
        edge = edges[min(self._map_edge_index, len(edges) - 1)]
        start = self._node_by_id(nodes, edge.get("from")) or nodes[0]
        end = self._node_by_id(nodes, edge.get("to")) or nodes[min(1, len(nodes) - 1)]
        sx, sy = self._node_xy(nodes, start)
        ex, ey = self._node_xy(nodes, end)
        edge_len = max(((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5, 1.0)
        if vision.confidence >= float(getattr(self.cfg.pid, "min_track_confidence", 0.18)):
            self._map_progress += max(0.0, motion.forward) * dt * 100.0
        while self._map_progress >= edge_len and self._map_edge_index < len(edges) - 1:
            self._map_progress -= edge_len
            self._map_edge_index += 1
            edge = edges[self._map_edge_index]
            start = self._node_by_id(nodes, edge.get("from")) or start
            end = self._node_by_id(nodes, edge.get("to")) or end
            sx, sy = self._node_xy(nodes, start)
            ex, ey = self._node_xy(nodes, end)
            edge_len = max(((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5, 1.0)
        ratio = clamp(self._map_progress / edge_len, 0.0, 1.0)
        x = sx + (ex - sx) * ratio
        y = sy + (ey - sy) * ratio
        theta = math.atan2(ey - sy, ex - sx)
        self._map_pose = {
            "ok": True,
            "mode": "topology_odometry",
            "edge_index": self._map_edge_index,
            "from": edge.get("from", ""),
            "to": edge.get("to", ""),
            "progress": ratio,
            "x": x,
            "y": y,
            "theta": theta,
            "lateral_error": vision.line_error,
            "confidence": min(1.0, max(0.0, vision.confidence)),
            "branches": list(vision.branches),
            "branch_offsets": vision.branch_offsets or {},
            "note": "无二维码/外部定位时，这是基于任务图和命令速度的粗略位置；岔路或颜色节点可用于重定位。",
        }

    def _node_by_id(self, nodes, node_id):
        for node in nodes:
            if node.get("id") == node_id:
                return node
        return None

    def _node_xy(self, nodes, node):
        if "x" in node and "y" in node:
            return float(node["x"]), float(node["y"])
        index = max(0, nodes.index(node)) if node in nodes else 0
        return float((index % 3) * 220), float((index // 3) * 118)
