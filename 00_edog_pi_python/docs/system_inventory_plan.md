# System Inventory And Cleanup Plan

## Current Blocker

The Windows USB Ethernet adapter was observed at `169.254.122.245/16`. Adding
`192.168.12.209/24` failed with access denied, so the robot was not reachable at
`192.168.12.1` from this session.

`192.168.137.1:22` accepted TCP but did not present a normal SSH banner, so it is
probably not the robot.

## Safe Inventory Procedure

1. Record current adapter configuration.
2. Temporarily add `192.168.12.209/24` to the USB Ethernet adapter.
3. Run `python scripts/readonly_inventory.py --host 192.168.12.1`.
4. Save output under `docs/remote_inventory_latest.txt`.
5. Restore the adapter to its previous state.

The inventory script is read-only. It checks system version, network, processes,
ports, services, startup files, project folders, and installed packages. It does
not use `sudo`, edit files, install packages, reboot, or stop services.

## Cleanup Direction

- Keep old robot image files and Windows-only tools in `alternative/`.
- Move redundant source copies and build outputs to `Orchard/`.
- Preserve `edog-brain`, `edog-track`, and `colorGroup.txt` backups before any
  remote deployment.
- Do not overwrite startup scripts until the Python runtime has passed dry-run,
  serial stop, and camera tests.

