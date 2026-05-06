# Legacy project issues

The old stack can work for emergency competition operation, but it is fragile.

## Main issues
- Application and backend are split across `edog-track*` and `edog-brain`, but there is no clean release boundary.
- Many build products, IDE files, autosaves, and copied directories live next to source code.
- Runtime configuration is stored in ad hoc files such as `colorGroup.txt` and shell command arguments.
- Network startup has IP conflicts between wired debug and WiFi AP mode.
- Operator commands are manual and repetitive, which increases the chance of starting the wrong copy.
- Recovery depends on rebooting, killing processes, and rerunning shell fragments.
- Serial protocol knowledge is buried in C++ code rather than a tested protocol module.
- The visual logic is difficult to test offline because it is tied to camera windows and Qt/C++ build flow.

## Replacement direction
- Python backend owns camera, state machine, gamepad, and serial output in one testable runtime.
- Frontend is only for tuning, preview, status, and logs.
- Deployment is release based: upload to `/home/pi/edog_pi_python/releases/<timestamp>` and switch `current`.
- Old C++ projects remain as archived references until Python has passed field tests.
