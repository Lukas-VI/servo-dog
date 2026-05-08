# 赛道地图录入与导入方案

## 当前状态

当前项目已经有 `task_graph`，可以描述任务节点和连线，但还没有独立的赛道地图文件管理系统。

现在实际可用的录入方式：

1. 打开 Web 调试台。
2. 进入“任务图”。
3. 手动新增节点、连线、条件和动作。
4. 点击保存配置。
5. 配置写入当前版本的 `config.yaml`。

这适合固定小赛道，但不适合长期维护多张地图。

## 建议的持久化目标

后续应新增：

```text
/home/pi/edog_pi_python/current/maps/
```

每张赛道一个 JSON：

```text
maps/race_track_v1.json
maps/test_track_left_branch.json
```

地图文件描述拓扑，而不是保存完整图像点云。

## 地图 JSON 建议格式

```json
{
  "name": "race_track_v1",
  "version": 1,
  "created_at": "2026-05-08",
  "nodes": [
    {"id": "start", "type": "start"},
    {"id": "fork_1", "type": "fork", "exits": ["left", "straight"]},
    {"id": "color_blue", "type": "color", "color": "blue", "action": "updais"},
    {"id": "finish", "type": "finish"}
  ],
  "edges": [
    {"from": "start", "to": "fork_1", "condition": "line_confidence>0.35"},
    {"from": "fork_1", "to": "color_blue", "choice": "left"},
    {"from": "color_blue", "to": "finish", "condition": "after_action"}
  ]
}
```

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

后续 Web 应支持：

- 上传 JSON。
- 从 `maps/` 列表选择。
- 将地图导入为 `config.yaml` 的 `task_graph`。
- 将当前 `task_graph` 导出为地图 JSON。

当前还没有完整实现地图导入/导出按钮，所以短期仍使用任务图编辑和 `config.yaml`。
