# RS232 归零与调脉宽恢复记录

## 结论

当前文档、本地源码和现场截图只确认了两层串口协议：

- 旧 `edog-brain` 到驱动板的高层运动协议：`/dev/serial0`，`9600`，`8N1`。
- 上位机 Action Designer 连接控制板的方式：RS232 串口，`9600`，`8N1`，但文档没有给出“pose 库 / 调脉宽 / 写入校准值”的逐关节私有帧格式。

所以现在不能盲目发“全部关节归零”的低层帧。把未知帧写进控制板可能导致关节猛动、校准区被错误覆盖，甚至让原始数据无法找回。

现场截图显示 Action Designer 的调脉宽反馈已经异常：部分关节为 `0`，部分字段显示很长的巨大数字或负数字符串。这不是正常脉宽。正常脉宽大致应在 `900..2100` 微秒。出现这种状态时不要点击“保存”，也不要把所有字段写成 `0`。

## 文档中已经确认的信息

- RS232 接线：机器狗端接口从上往下依次是 `rx`、`tx`、`gnd`。
- RS232 公头接法：`rxd -> 机器狗 tx`，`txd -> 机器狗 rx`，`sg -> 机器狗 gnd`。
- 上位机连接参数：`9600`，`8` 数据位，`none` 校验，`1` 停止位。
- “pose 库 -> 添加 -> 调脉宽”后，上位机会让四肢直立锁死，并显示每个关节的反馈脉宽。
- 示例截图里的反馈值是绝对脉宽，不是 Python 项目当前使用的速度/姿态命令：
  - 左前腿上 `1036`
  - 左前腿中 `1398`
  - 左前腿下 `1941`
  - 右前腿上 `1924`
  - 右前腿中 `1488`
  - 右前腿下 `954`
  - 左后腿上 `1954`
  - 左后腿中 `1448`
  - 左后腿下 `1911`
  - 右后腿上 `1046`
  - 右后腿中 `1498`
  - 右后腿下 `1114`
  - 头部 `1487`
  - 腰部 `1540`

## 已知高层帧

这些帧属于旧 `edog-brain` 层，可以安全复核，但它们不是逐关节调脉宽帧：

- 停止：`8F 00 01 0D 0E FF`
- 动作调用：`8F 51 01 <ActionID> <Sum> FF`
- 运动帧：`8F 25 16 02 <forward:f32le> <side:f32le> <yaw:f32le> <height:u8> <roll:f32le> <pitch:f32le> <Sum> FF`

零速度、中立姿态、站高 `144` 的高层帧可以用脚本生成。它只要求控制板进入站立/中立控制输入，不会修改每个关节的 EEPROM 校准值。

## 现场恢复脚本

Windows 本机不一定装了 `pyserial`，所以同时提供 PowerShell 版本。现场识别到的 RS232 是 `Dtech USB-Serial Controller (COM3)`。

列出本机串口：

```powershell
.\00_edog_pi_python\scripts\rs232_recovery.ps1 -ListPorts
```

只打印停止帧，不写串口：

```powershell
.\00_edog_pi_python\scripts\rs232_recovery.ps1 -Port COM3 -Stop
```

确认机器狗被手扶、腿部没有压住异物后，实际发送停止帧：

```powershell
.\00_edog_pi_python\scripts\rs232_recovery.ps1 -Port COM3 -Stop -Force -Repeat 3
```

只打印零速度中立站立帧：

```powershell
.\00_edog_pi_python\scripts\rs232_recovery.ps1 -Port COM3 -NeutralStand -Height 144
```

实际发送零速度中立站立帧：

```powershell
.\00_edog_pi_python\scripts\rs232_recovery.ps1 -Port COM3 -NeutralStand -Height 144 -Force -Repeat 3
```

## Python 版本

列出本机串口：

```powershell
python .\00_edog_pi_python\scripts\rs232_recovery.py --list-ports
```

只打印停止帧，不写串口：

```powershell
python .\00_edog_pi_python\scripts\rs232_recovery.py --port COM7 --stop
```

确认机器狗被手扶、腿部没有压住异物后，实际发送停止帧：

```powershell
python .\00_edog_pi_python\scripts\rs232_recovery.py --port COM7 --stop --force --repeat 3
```

只打印零速度中立站立帧：

```powershell
python .\00_edog_pi_python\scripts\rs232_recovery.py --port COM7 --neutral-stand --height 144
```

实际发送零速度中立站立帧：

```powershell
python .\00_edog_pi_python\scripts\rs232_recovery.py --port COM7 --neutral-stand --height 144 --force --repeat 3
```

如果后续从上位机抓到或从厂商文档拿到逐关节调脉宽帧，可以先用 dry-run 打印，再用 `--raw-hex` 发送：

```powershell
python .\00_edog_pi_python\scripts\rs232_recovery.py --port COM7 --raw-hex "8F 00 01 0D 0E FF"
```

实际发送 raw frame 必须加 `--force`：

```powershell
python .\00_edog_pi_python\scripts\rs232_recovery.py --port COM7 --raw-hex "8F 00 01 0D 0E FF" --force
```

## 下一步如何拿到真正的逐关节写入协议

优先级从高到低：

1. 找到资料包里的 `ActionDesigner新版上位机` 可执行文件和“上位机使用说明”，检查是否带协议说明、配置文件或日志。
2. 用串口抓包工具监听 Action Designer 点击“读取 / 调脉宽 / 保存 / 调占空比”时发出的帧。
3. 如果上位机因为占空比溢出无法写入，先抓“连接”和“读取”的帧，确认帧头、长度、命令字、校验方式。
4. 再实现一个受限的 `joint_pwm_write` 子命令，按关节名写入单个值，并且默认限制在 `900..2100` 微秒范围内。

在逐关节协议确认前，不能把所有关节写成 `0`。对舵机来说 `0` 常常不是中位，而是无效脉宽或断脉冲。
