# Repository Organization

## Mainline

`00_edog_pi_python/` is the new front-of-repo Python implementation. It should be
the only active development target.

## Reference

`00_edog_pi_python/reference/132_legacy_candidate/` contains the most useful old
C++ contest implementation found in this workspace. It is retained as behavior
reference only.

## Orchard

`Orchard/` contains old or redundant material:

- `edog-track5_broken_root_copy/`: root copy with a damaged `main.cpp`.
- `archives/`: original zip archives.
- `vscode_legacy_cpp/`: old C++ editor settings.

## alternative

`alternative/` contains supporting tools and Windows-era resources:

- ActionDesigner upper-computer app and action-design assets.
- PL2303 / RS232 driver packages bundled with the old materials.
- VMware installer.

## Rule Going Forward

Do not edit or deploy anything in `Orchard/` or `alternative/` as mainline code.
Copy small verified facts into `docs/` or tests when needed, then keep new work in
`00_edog_pi_python/`.

