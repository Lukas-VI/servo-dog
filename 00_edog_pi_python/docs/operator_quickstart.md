# 比赛操作快速说明

## 连接

1. 电脑用网线连接树莓派。
2. 机器有线地址：`192.168.12.1`。
3. SSH：

```bash
ssh pi@192.168.12.1
```

密码：`123456`。

Web 调试台：

```text
http://192.168.12.1:8080
```

## 从 Windows 部署

在 `D:\AAA6` 执行：

```powershell
.\00_edog_pi_python\scripts\deploy_to_pi.ps1
```

部署脚本会上传到：

```text
/home/pi/edog_pi_python/releases/<时间戳>
```

并切换当前版本：

```text
/home/pi/edog_pi_python/current
```

## 开机服务

部署后刷新 systemd：

```powershell
python .\00_edog_pi_python\scripts\install_systemd_services.py --host 192.168.12.1 --user pi --password 123456
```

开机自启的服务：

```bash
sudo systemctl status edog-debug.service
sudo systemctl restart edog-debug.service
```

`edog-debug.service` 负责 Web 调试台。

串口控制服务默认安装但不自启：

```bash
sudo systemctl status edog-runner.service
sudo systemctl start edog-runner.service
sudo systemctl stop edog-runner.service
```

只有台架测试确认安全后，才考虑：

```bash
sudo systemctl enable edog-runner.service
```

## 手动运行

Dry-run，不写串口：

```bash
cd /home/pi/edog_pi_python/current
./run_dry.sh --mode track
```

真实串口运行：

```bash
cd /home/pi/edog_pi_python/current
./run_serial.sh --mode stop
```

只使用 Web/手柄控制、不打开摄像头：

```bash
cd /home/pi/edog_pi_python/current
./run_control_only.sh --mode stop
```

开始自动巡线：

```bash
./run_serial.sh --mode track
```

串口参数：

```text
/dev/serial0, 9600, 8N1
```

## 手柄三种状态

在 Web 手柄面板或 `config.yaml` 设置：

```yaml
gamepad:
  transport: usb
```

合法值：

- `usb`：树莓派直接读取 USB 或 2.4G USB 接收器手柄。
- `disabled`：关闭手柄。
- `web`：通过 Web 接口下发手柄命令。

Web 手柄接口：

```http
POST http://192.168.12.1:8080/api/gamepad
GET  http://192.168.12.1:8080/api/gamepad
```

## 手柄优先级

运行时优先级：

1. 急停。
2. 手动保持遥控。
3. 一次性动作键。
4. 模式切换键。
5. 自动视觉巡线。

默认 Xbox 风格映射：

- `B`：急停，强制发送 stop 帧。
- `LB`：按住手动遥控。
- 左摇杆前后：前进/后退。
- 左摇杆左右：横移。
- 右摇杆左右：滚转。
- 右摇杆前后：俯仰。
- 左扳机：降低高度。
- 右扳机：升高高度。
- `A`：切换到 `track`。
- `X`：切换到 `stop`。

步态、动作键位、模式键位都可以在 Web 手柄面板保存到 `config.yaml`。

## 调试流程

1. 打开 `http://192.168.12.1:8080`。
2. 查看实时摄像头。
3. 调 HSV 阈值。
4. 调 PID 参数。
5. 调岔路参数。
6. 调手柄通路和键位。
7. 保存配置。
8. 重启串口运行服务：

```bash
sudo systemctl restart edog-runner.service
```

## 开始比赛任务

推荐流程：

1. 开机。
2. 确认 Web 调试台可访问。
3. 确认摄像头画面正常。
4. 确认手柄通路是 `usb`、`disabled` 或 `web` 中的预期值。
5. 启动串口服务：

```bash
sudo systemctl start edog-runner.service
```

`edog-runner.service` 默认使用 `run_control_only.sh`，也就是不抢 Web 调试台的摄像头，主要负责手柄、Web 初始化、开始、结束、动作和站高控制。需要自动视觉巡线时，停止 Web 摄像头服务或改用 `run_serial.sh --mode track` 独占摄像头。

6. 放置机器人。
7. 用 Web 的“开始巡线”或手柄按 `A` 进入 `track`。如果要自动视觉闭环，命令行直接：

```bash
cd /home/pi/edog_pi_python/current
./run_serial.sh --mode track
```

8. 任意时刻按 `B` 急停。
