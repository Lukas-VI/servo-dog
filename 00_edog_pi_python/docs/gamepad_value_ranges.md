# 手柄配置字段和值域

所有手柄字段都在 `config.yaml` 的 `gamepad:` 段。

## 手柄通路

`transport` 有三种合法值：

- `usb`：树莓派本机通过 pygame 读取 USB 或 2.4G USB 接收器手柄。
- `disabled`：禁用手柄输入，只跑自动视觉或 dry-run。
- `web`：运行时读取 Web 调试服务写入的命令文件。

`web_command_path` 是 Web 手柄命令文件路径，默认：

```text
/tmp/edog_web_gamepad.json
```

Web 通讯接口：

```http
POST http://192.168.12.1:8080/api/gamepad
GET  http://192.168.12.1:8080/api/gamepad
```

POST 示例：

```json
{
  "manual_enabled": true,
  "emergency_stop": false,
  "selected_mode": "track",
  "selected_action": "",
  "motion": {
    "forward": 0.2,
    "side": 0.0,
    "yaw": 0.0,
    "roll": 0.05,
    "pitch": -0.04,
    "stand_height": 144,
    "gait": 2
  }
}
```

Web 命令超时后会自动视为未连接，避免浏览器断开后保留旧速度。

## 轴和按钮字段

- `axis_forward`、`axis_side`、`axis_roll`、`axis_pitch`、`axis_left_trigger`、`axis_right_trigger`：整数轴编号，值域 `0..15`。
- `button_emergency_stop`、`button_manual`：整数按钮编号，值域 `0..31`。
- `mode_buttons`：按钮编号 `0..31` 到模式名的映射。默认 `A=track`、`X=stop`、`Y=byroad_a`、`RB=byroad_b`，用于起点快捷选择任务。
- `action_buttons`：按钮编号 `0..31` 到动作名的映射。

pygame 摇杆轴原始值域是 `-1.0..1.0`。扳机会换算成 `0.0..1.0`，左扳机降低高度，右扳机升高高度。

## 手动运动字段

- `max_forward`：`0.0..0.8`，左摇杆前后最大速度。
- `max_side`：`0.0..0.8`，左摇杆左右最大速度。
- `max_roll`：`0.0..0.8`，右摇杆左右最大滚转。
- `max_pitch`：`0.0..0.8`，右摇杆前后最大俯仰。
- `deadzone`：`0.0..0.35`，摇杆死区。

映射关系：

- 左摇杆前后 -> `forward`
- 左摇杆左右 -> `side`
- 右摇杆左右 -> `roll`
- 右摇杆前后 -> `pitch`
- 左右扳机 -> `stand_height`

`yaw` 当前仍由自动巡线控制。若要纯手动原地转向，需要再增加一个手柄轴到 `yaw` 的配置项。

## 高度和步态

- `min_height`：整数，建议 `60..180`。
- `max_height`：整数，建议 `100..220`。
- `height_step`：`0.2..8.0`，满扳机时每个控制周期改变的高度单位。
- `gait`：整数，值域 `0..15`，默认 `2`，对应旧协议里的 trot 步态字节。

## 合法模式值

- `stop`
- `track`
- `byroad_a`
- `byroad_b`
- `lean_left`
- `lean_right`
- `updais`
- `manual`

## 合法动作值

- `upstair`
- `downstair`
- `updais`
- `lean`
- `lean_left`
- `lean_right`
- `leg_left`
- `leg_right`

## 优先级

运行时优先级固定为：

1. 急停。
2. 手动保持遥控。
3. 一次性动作键。
4. 模式切换键。
5. 自动视觉状态机。

模式键和动作键按“上升沿”触发，长按不会每一帧重复发送动作。
