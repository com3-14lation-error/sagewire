# sagewire

Avionics wiring and system architecture documentation for **Sage**.

This repository holds the wiring definitions (connections, cable specifications, bill of materials) and the system architecture diagram for Sage's avionics.

## Status

Work in progress.

## TODO

Open design items. The detail for each one is in the `TODO:` comments of the harness files (`grep -rn TODO harness/` lists them all).

1. Battery to PDB: battery connector, cable and lugs are not decided (the PDB battery input is bolted, ring lugs).
2. Motor boom connector and wiring.
3. ESC to motor: phase lead gauge, length and connector.
4. ESC capacitor count: the APD table says one 330 uF 50 V capacitor per ESC, the harness models two.
5. Servo CAN termination (?): confirm by measuring whether the Zeus servos have a built-in 120 ohm. Also the far end of the CAN1 bus (airspeed sensor).
6. DB-25 fix (model, shell, contacts, hood, final pin map) and M5 plug fix (part number, contacts, current rating).
7. RF voltage drop: the radio 5 V supply (W_RF_03) has almost no margin at 1.5 m and fails at 2 m. Extend the 16 AWG UBEC leads close to the radio and split into the 26 AWG tails, or shorten the run.
8. GSM module power: the two 5G dongles are powered from the Jetson USB ports for now (about 2 A each, over the port rating). Move them to a BEC.
9. GSM and RF antennas not fixed (eight 5G antennas for the two dongles, two MMCX antennas for the radio).
10. VTOL motor power gauge: 10 AWG against about 80 A design current. 8 AWG is under consideration (check that it fits the XT90 cups and PDB pads, or move to XT150/AS150).
11. ESC voltage margin: a 12S pack is 50.4 V at full charge, the ESC maximum and the capacitor rating are 50 V.
12. 5G modem choice (Telit FN990 variant): check Airtel NSA band combinations, Jio SA on n28 and n78, and that the Waveshare dongle board works with a Telit module.
13. Voltage drop on the servo power (26 AWG, about 1.9 V at 2.2 A over 3 m) and on the LED wires (22 AWG, wingtip runs).
14. BEC output voltages: set and verify with a meter before the first power-up; decide 5 V or 6 V on the radio and LED BEC.
15. Parts still without a model or part number: USB to TTL converter, Jetson module memory size, Sierra GPS, SwiftWing CAN splitter, Vector Technics motors, MMCX plugs, RJ45 plug for the radio, USB breakout boards, LED leads.
16. Assumed connector details to check on the real parts: Cube Orange+ ADS-B carrier ports, LightWare Pixhawk adapter pin order (and whether W_FC_04 is still needed), Sierra GPS and airspeed pin order, Jetson board power pads (polarity and size, gauge of W_CEL_08).
17. Forward motor (VT4130 FW) is provisional.
18. All cable lengths are placeholders (0) until the layout analysis. DShot rate and the maximum cable length on the long wing runs follow from it.

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

The actuators are split into seven files: for each wing a motors file (`actuators_left_motors_system.yaml`, `actuators_right_motors_system.yaml`: power chain, ESCs, motors, capacitors), a wing-side file (`actuators_left_wing_system.yaml`, `actuators_right_wing_system.yaml`: DB-25 plug, servos, LEDs, ESC signal pads) and a fuselage-side file (`actuators_left_fuselage_system.yaml`, `actuators_right_fuselage_system.yaml`: DB-25 socket, UBEC ports, Cube AUX and MAIN, CAN splitter ports), plus `actuators_frw_system.yaml` (forward-thrust motor). `python scripts/make_wire_list.py` regenerates `docs/wire_list.md` from all the harnesses.

Reports and the GitHub Pages site (`index.html` lists the BOM and the wire list first, then each harness):

```
python scripts/render.py                                  # harness pages and per-harness BOMs into build/
python scripts/make_bom.py                                # consolidated BOM: build/bom.html and build/bom.csv
.venv/Scripts/python scripts/make_wire_list.py            # wire list: build/wire_list.html (and docs/wire_list.md)
python scripts/publish_pages.py --push                    # publish build/ to the gh-pages branch
```

`make_bom.py` merges the BOM of every harness (same description, manufacturer and MPN are added together). `make_wire_list.py` needs PyYAML, so run it with the project venv. The wire comments in the wire list are written in `scripts/make_wire_list.py`, so add a line there for each new cable.

Needs Graphviz on the PATH. In pin lists, quote labels that YAML would read as booleans (`"NO"`, `"ON"`, `"Y"`).
