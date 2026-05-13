param(
    [string]$Port = "COM3",
    [int]$Baud = 9600,
    [switch]$ListPorts,
    [switch]$Stop,
    [switch]$NeutralStand,
    [int]$Height = 144,
    [string]$RawHex = "",
    [int]$Repeat = 1,
    [double]$Interval = 0.08,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Convert-HexToBytes {
    param([string]$Hex)
    $clean = $Hex -replace "0x", " " -replace "0X", " " -replace ",", " "
    $parts = $clean -split "\s+" | Where-Object { $_ }
    [byte[]]($parts | ForEach-Object { [Convert]::ToByte($_, 16) })
}

function Get-Checksum {
    param([byte[]]$Payload)
    $sum = 0
    foreach ($b in $Payload) {
        $sum = ($sum + $b) -band 0xFF
    }
    [byte]$sum
}

function Convert-FloatLe {
    param([single]$Value)
    [BitConverter]::GetBytes($Value)
}

function New-StopFrame {
    [byte[]]$payload = 0x00, 0x01, 0x0D
    [byte[]](0x8F) + $payload + [byte[]](Get-Checksum $payload) + [byte[]](0xFF)
}

function New-NeutralStandFrame {
    param([int]$StandHeight)
    $bytes = New-Object System.Collections.Generic.List[byte]
    $bytes.Add(0x25)
    $bytes.Add(0x16)
    $bytes.Add(0x02)
    $bytes.AddRange([byte[]](Convert-FloatLe 0.0))
    $bytes.AddRange([byte[]](Convert-FloatLe 0.0))
    $bytes.AddRange([byte[]](Convert-FloatLe 0.0))
    $bytes.Add([byte]($StandHeight -band 0xFF))
    $bytes.AddRange([byte[]](Convert-FloatLe 0.0))
    $bytes.AddRange([byte[]](Convert-FloatLe 0.0))
    $payload = [byte[]]$bytes.ToArray()
    [byte[]](0x8F) + $payload + [byte[]](Get-Checksum $payload) + [byte[]](0xFF)
}

function Format-FrameHex {
    param([byte[]]$Frame)
    ($Frame | ForEach-Object { $_.ToString("X2") }) -join " "
}

function Write-Frame {
    param([byte[]]$Frame)
    $serial = [System.IO.Ports.SerialPort]::new($Port, $Baud, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One)
    $serial.WriteTimeout = 250
    $serial.ReadTimeout = 250
    try {
        $serial.Open()
        for ($i = 1; $i -le [Math]::Max(1, $Repeat); $i++) {
            $serial.Write($Frame, 0, $Frame.Length)
            Write-Host "write ${i}/${Repeat}: $(Format-FrameHex $Frame)"
            if ($i -lt $Repeat -and $Interval -gt 0) {
                Start-Sleep -Seconds $Interval
            }
        }
    }
    finally {
        if ($serial.IsOpen) {
            $serial.Close()
        }
        $serial.Dispose()
    }
}

if ($ListPorts) {
    Get-CimInstance Win32_PnPEntity |
        Where-Object { $_.Name -match "COM|Serial|UART|FT232|PL2303|CH340|USB-Serial" } |
        Select-Object Name, Status, DeviceID |
        Format-Table -AutoSize
    exit 0
}

if ($Stop) {
    $frame = New-StopFrame
    $mode = "known stop"
}
elseif ($NeutralStand) {
    $frame = New-NeutralStandFrame -StandHeight $Height
    $mode = "known neutral stand height=$Height"
}
elseif ($RawHex.Trim().Length -gt 0) {
    $frame = Convert-HexToBytes $RawHex
    $mode = "raw hex"
}
else {
    throw "Choose -ListPorts, -Stop, -NeutralStand, or -RawHex."
}

Write-Host "mode: $mode"
Write-Host "port: $Port, baud: $Baud, 8N1"
Write-Host "frame: $(Format-FrameHex $frame)"

if (-not $Force) {
    Write-Host "dry-run only. Add -Force after physically supporting the robot."
    exit 0
}

Write-Frame $frame
