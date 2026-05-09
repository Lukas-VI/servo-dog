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

默认打开的是“控制台”主页：

- “左住户任务”：起点选择左岔，随后自动循迹；看到紫色/棕色条带后按任务逻辑自动倾斜送球。
- “右住户任务”：起点选择右岔，随后自动循迹；看到紫色/棕色条带后按任务逻辑自动倾斜送球。
- “直行循迹”：不预选左右住户，只执行基础自动循迹。
- “结束/急停”：停止自动进程并发送 stop。

“调参”页只放 HSV、ROI、PID、手柄映射、任务图等细项，比赛操作时尽量留在控制台主页。

无线 AP 调试网：

```text
SSID: edog-ap
Password: EDOG-Q9gub1Ss7roSRk
Web: http://192.168.13.1:8080
SSH: ssh pi@192.168.13.1
```

当前板载 `wlan0` 用来开 AP，有线 `eth0` 保持 `192.168.12.1/24`。如果要让机器狗一边开 AP 给电脑调试、一边连接实验室 Wi-Fi 或手机热点，建议增加一个 USB Wi-Fi 网卡；Xbox 2.4G 接收器不是 Wi-Fi 网卡。

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
- 默认不再要求按住 `LB`，摇杆有输入就进入手动遥控；急停优先级最高。
- 左摇杆左右：偏航。
- 左摇杆上下：高度油门，摇杆位置会维持成一个固定站高值。
- 右摇杆前后：前进/后退。
- 右摇杆左右：横移，当前已做左右反向修正。
- 滚转/俯仰默认禁用。
- `A`：起点选择直行/基础循迹 `track`。
- `X`：切换到 `stop`。
- `Y`：起点选择左住户任务 `byroad_a`。
- `RB`：起点选择右住户任务 `byroad_b`。

步态、动作键位、模式键位都可以在 Web 手柄面板保存到 `config.yaml`。

## 调试流程

1. 打开 `http://192.168.12.1:8080`。
2. 查看实时摄像头。
3. 调 HSV 阈值。
4. 点击“轨道提取”，确认绿色掩膜只覆盖跑道/轨道，不覆盖地图边缘、机架、桌椅。
   - `ROI 起始比例` 越小，看得越远；越大，只看近处下半画面。
   - `上方门控宽度` / `底部门控宽度` 控制梯形地面区域，调大可以放宽视野。
   - `排除背景` 可以临时关闭，用来比较背景过滤前后的效果。
5. 调 PID 参数。
6. 调岔路参数。
   - `目标通道融合` 越高，岔路中越直接追左/直/右候选通道中心。
   - `岔路速度系数` 控制过岔路时的轻微降速，比赛冲速度时可接近 `1.0`。
   - `岔路锁定秒数` 让目标岔路短时间保持，避免识别一帧丢失后方向抖动。
7. 调手柄通路和键位。
8. 在“任务图”里保存/读取地图；运行时反馈里的 `地图位置` 会显示当前边和进度。
9. 保存配置。
10. 重启串口运行服务：

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
