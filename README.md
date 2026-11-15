# sagewire

Avionics wiring and system architecture documentation for **Sage**.

This repository holds the wiring definitions (connections, cable specifications, bill of materials) and the system architecture diagram for Sage's avionics.

## Status

Work in progress.

## Detailed wiring (WireViz)

One YAML file per system in `harness/`. Render one with:

```
wireviz -f hpst -o build harness\power_system.yaml
```

Or use the helper, which renders everything (or just the named harnesses) into `build/`:

```
python scripts/render.py
python scripts/render.py power rf --open
```

The actuators are split into three files: `actuators_left_wing_system.yaml`, `actuators_right_wing_system.yaml` and `actuators_frw_system.yaml` (forward-thrust motor). `python scripts/make_wire_list.py` regenerates `docs/wire_list.md` from all the harnesses.

Needs Graphviz on the PATH. In pin lists, quote labels that YAML would read as booleans (`"NO"`, `"ON"`, `"Y"`).
