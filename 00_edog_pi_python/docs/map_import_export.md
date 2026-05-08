# 赛道地图录入与导入方案

## 当前状态

当前项目已经有 `task_graph`，可以描述任务节点和连线；Web 调试台的“任务图”页也已经支持把当前任务图保存/读取为 `maps/*.json`。

现在实际可用的录入方式：

1. 打开 Web 调试台。
2. 进入“任务图”。
3. 手动新增节点、连线、条件和动作。
4. 点击“保存地图”写入当前 release 的 `maps/<name>.json`。
5. 点击“保存配置”会把当前任务图写入 `config.yaml`。

这适合固定小赛道，但不适合长期维护多张地图。

## 建议的持久化目标

当前保存目录：

```text
/home/pi/edog_pi_python/current/maps/
```

每张赛道一个 JSON：

```text
maps/race_track_v1.json
maps/test_track_left_branch.json
```

地图文件描述拓扑，而不是保存完整图像点云。

## 地图 JSON 格式

```json
{
  "name": "race_track_v1",
  "version": 1,
  "created_at": "2026-05-08",
  "mode": "line_topology",
  "branch_default": "straight",
  "nodes": [
    {"id": "start", "label": "Start", "type": "track", "color": "black", "action": "", "x": 0, "y": 0},
    {"id": "fork_1", "label": "Fork 1", "type": "fork", "color": "black", "action": "", "x": 120, "y": 0},
    {"id": "finish", "label": "Stop", "type": "stop", "color": "black", "action": "stop", "x": 240, "y": 80}
  ],
  "edges": [
    {"from": "start", "to": "fork_1", "condition": "line_confidence>0.35"},
    {"from": "fork_1", "to": "finish", "condition": "choice:right"}
  ]
}
```

`x/y` 是可选字段。没有填写时，运行时会按任务图顺序生成粗略坐标；填写后，`runtime_status.map_pose` 会用这些坐标显示当前位置。

## 录入方式

### 手动录入

适合比赛前已知赛道：

1. 在 Web 地图页创建地图。
2. 添加起点。
3. 按赛道顺序添加岔路节点。
4. 为每个岔路选择出口：`left`、`straight`、`right`。
5. 添加颜色任务或动作节点。
6. 保存为 JSON。

### 试跑录入

适合赛道还不确定：

1. 低速 dry-run 或限速运行。
2. 视觉检测到高置信岔路时暂停或标记。
3. 操作者在 Web 端确认该节点有哪些出口。
4. 保存拓扑。
5. 第二次运行按地图执行。

## 导入方式

Web 当前支持：

- “保存地图”：把当前任务图保存为 JSON。
- “读取地图”：读取同名 JSON 并导入到当前任务图。
- “导出地图 JSON”：复制当前地图 JSON，便于手工备份。

## 粗定位说明

没有二维码、AprilTag、轮速计或 IMU 融合时，系统不能获得真正全局绝对位姿。当前实现提供的是“任务图绝对坐标里的粗定位”：

- `runtime_status.map_pose.from/to`：当前认为所在的任务图边。
- `runtime_status.map_pose.progress`：沿当前边的进度 `0..1`。
- `runtime_status.map_pose.x/y/theta`：基于任务图坐标和命令速度积分的粗略位置。
- `runtime_status.map_pose.lateral_error`：视觉巡线横向误差，可用于判断是否偏离赛道。

要让定位更稳定，建议在地图中录入岔路节点、颜色节点或动作节点；运行时检测到这些事件后，可以把当前位置重定位到对应节点。
