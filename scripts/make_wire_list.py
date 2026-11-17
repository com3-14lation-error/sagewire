"""Generate the wire list from harness/*.yaml.

Usage: python scripts/make_wire_list.py [repo_root]   (default: the repo this script is in)

Writes docs/wire_list.md (local notes) and build/wire_list.html (the page for GitHub Pages).
Needs PyYAML (in the project venv: .venv/Scripts/python scripts/make_wire_list.py).
"""
import yaml, glob, os, sys
from reports_html import esc, page, table

root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = {}
def c(ids, text):
    for i in ids:
        C[i] = text

c(["W_PWR_01"], "12 V KDE UBEC's own factory input leads (about 0.21 m). Keep 16 AWG if extended. Placeholder pad pair ESC7 on the PDB.")
c(["W_PWR_02"], "5 V KDE UBEC's own factory input leads (about 0.21 m). Keep 16 AWG if extended. Placeholder pad pair ESC8 on the PDB.")
c(["W_PWR_03"], "Plain two-wire contact; polarity does not matter.")
c(["W_PWR_04"], "Capacitor leads, short as possible. 220 uF 100 V capacitor across the battery bolts (J2); not yet picked.")
c(["W_PWR_05","W_PWR_06","W_PWR_07","W_PWR_08"], "About 75-80 A at full throttle per motor; 8 AWG if the run is long or hot. Check fit on the PDB pads and XT90 cups. PDB pad pair follows the motor number.")
c(["W_PWR_09"], "Expected up to about 80 A. Keep short (APD: long ESC input wires cause braking spikes). PDB pad pair ESC5.")
c(["W_ACT_01","W_ACT_02","W_ACT_03","W_ACT_04"], "Same 10 AWG as the fuselage side. Keep short (APD: more capacitance beyond 12 cm). 8 AWG if long or hot.")
c(["W_ACT_05","W_ACT_06","W_ACT_07","W_ACT_08","W_ACT_09"], "Motor's own leads, gauge unknown (not in the listing); use 10 AWG if ever extended. Phase order only sets spin direction.")
c(["W_ACT_10","W_ACT_12","W_ACT_19","W_ACT_21"], "26 AWG so it fits the M5 plug cup. Voltage drop about 1.8 V at the 2.2 A peak over 3 m one way (6 m loop). Servo takes 7-15 V.")
c(["W_ACT_11","W_ACT_13","W_ACT_20","W_ACT_22"], "Twisted pair. DB-25 CAN pins are adjacent. Servos have no built-in termination (mostly confirmed, not yet measured).")
c(["W_ACT_14","W_ACT_15","W_ACT_23","W_ACT_24"], "Motor-tip StrobeIT, 0.8 A peak at 5 V. Pad order is GND, signal, 5 V (mirrored vs the Pro); wired by pin so polarity is right.")
c(["W_ACT_16","W_ACT_25"], "Wingtip StrobeIT-Pro: pad order is 5 V, signal, GND. 0.8 A peak.")
c(["W_ACT_17","W_ACT_18","W_ACT_26","W_ACT_27"], "T = telemetry, S = signal, then signal GND. Twist the trio (APD). Left ESC 1 = motor 3, ESC 2 = motor 2; right ESC 1 = motor 1, ESC 2 = motor 4.")
c(["W_ACT_28","W_ACT_29","W_ACT_30","W_ACT_31"], "CAN_H, CAN_L (twist) and GND to splitter pins 2, 3, 4. Pin 1 (5 V) empty. GND is the same DB-25 pin as the servo power return.")
c(["W_ACT_32","W_ACT_33","W_ACT_34","W_ACT_35","W_ACT_36","W_ACT_37","W_ACT_38","W_ACT_39","W_ACT_40","W_ACT_41"], "Not a wire: the capacitor's own legs soldered to the ESC pads. 330 uF 50 V capacitors from the ESC box; the harness models two per ESC in parallel, the APD table says one (count to be checked). Legs as short as possible.")
c(["W_ACT_42","W_ACT_43","W_ACT_44","W_ACT_45"], "12 V UBEC servo port to the fuselage DB-25 servo power pins. 22 AWG, short. Each servo has its own port (3.3 A max, servo burst 2.2 A).")
c(["W_ACT_46","W_ACT_47","W_ACT_48","W_ACT_49","W_ACT_50","W_ACT_51"], "5 V UBEC servo port to the fuselage DB-25 LED power pins (5 V and GND). 22 AWG, short. LED 0.8 A peak, port 3.3 A max.")
c(["W_ACT_52","W_ACT_53","W_ACT_54","W_ACT_55"], "Cube AUX OUT (DShot-capable) signal and ground to the fuselage DB-25 ESC pins, then on through the wing cable. Twist the pair. Long run: DShot margin to check. Telemetry T not wired.")
c(["W_ACT_56"], "Cube AUX 5 signal and ground straight to the forward ESC. Twist the pair. Telemetry T not wired.")
c(["W_ACT_57","W_ACT_58","W_ACT_59","W_ACT_60","W_ACT_61","W_ACT_62"], "Cube MAIN OUT PWM and ground to the fuselage DB-25 LED pins. Slow servo PWM, so run length is not critical. Ground joins the UBEC return on the same DB-25 pin. LEDs could share one output if needed.")
c(["W_FC_01"], "26 AWG is the one size both crimps take (GH 26-30, CLIK-Mate 22-26). Load well under 1 A. Two 5 V, current sense, voltage sense, two GND.")
c(["W_FC_02"], "GPS draws up to 250 mA. Twist CAN_H/CAN_L. GPS is not the end node (CAN_TERM = 0).")
c(["W_FC_03"], "Daisy chain behind the GPS. About 50 mA. Expected long: keep CAN twisted, consider shielding. Airspeed pin order is assumed; far-end termination undecided (Sierra default is off).")
c(["W_FC_04"], "120 mA typical, 250 mA at start-up: about 0.07 V per metre of cable on 26 AWG. The sensor end is the LightWare Pixhawk adapter (the SUR housing takes 32 AWG only): recheck the gauge and whether this wire is needed once the adapter connector is known.")
c(["W_FC_05"], "CAN_H, CAN_L (twist) and GND to splitter port 1. 5 V pin not wired.")
c(["W_CEL_01"], "Supplied by SIYI (housing to RJ45 plug), not bought; gauge is the camera cable's own. Two twisted pairs, crossover: camera RX pair lands on RJ45 1/2, TX pair on 3/6.")
c(["W_CEL_02","W_CEL_03"], "VBUS, USB 2.0 data pair (twist) and GND. Dongle needs about 2 A from the Jetson USB jack (check the port limit), so 22 AWG for the whole cable.")
c(["W_CEL_04"], "Two wires per polarity: red pair to the two power pins, black pair to the two GND pins, joined at the XT30 pin. Power input is 3S-6S, fed 12 V from the 12 V UBEC (W_CEL_07). Supplied by SIYI (housing to XT30U-M), not bought; gauge is the camera cable's own.")
c(["W_CEL_06"], "12 V UBEC factory HP output leads (yellow/black, about 0.21 m) to the XT30U-F on the Jetson power path. About 4.8 A worst case. Keep 16 AWG if extended.")
c(["W_CEL_08"], "XT30U-M pigtail soldered straight onto the Jetson base board power pads. About 4.8 A worst case (6 A with a 40 W module). 18 AWG is a placeholder; the pad size sets the real limit.")
c(["W_CEL_07"], "12 V UBEC servo port 5 to the camera XT30 female. Camera is 1 A peak; port limit 3.3 A.")
c(["W_CEL_05"], "3.3 V UART (MAVLink). Yellow = Cube TX to converter RXD, green = Cube RX from converter TXD. Converter and its UART connector not chosen; 28 AWG is a placeholder.")
c(["W_RF_02"], "Two twisted pairs (T568B colours), crossover: radio RX pair lands on RJ45 1/2, TX pair on 3/6. Radio port is 100 Base-T, so RJ45 pins 4, 5, 7, 8 are empty. Gauge is a placeholder; shield undecided.")
c(["W_RF_03"], "5 V UBEC HP leads to radio port 4: three wires per polarity (a GH contact is 1 A). About 0.2 V drop per 1.5 m at 1.6 A against a 0.25 V budget (radio is 5 V +/- 5 %): keep it short.")
c(["W_RF_01"],"3.3 V UART. Yellow = Cube TX to radio RX, green = Cube RX from radio TX. Shield or twist if the run is long or noisy.")

def build_rows():
    rows = []
    for f in sorted(glob.glob(os.path.join(root, "harness", "*.yaml"))):
        d = yaml.safe_load(open(f, encoding="utf-8"))
        ends = {}
        for conn in d.get("connections", []):
            items = [it for it in conn if isinstance(it, dict)]
            names = [list(it.keys())[0] for it in items]
            for idx, n in enumerate(names):
                if n in d.get("cables", {}):
                    prev = names[idx-1] if idx > 0 else "?"
                    nxt = names[idx+1] if idx+1 < len(names) else "?"
                    ends.setdefault(n, []).append((prev, nxt))
        for k, v in d.get("cables", {}).items():
            g = v.get("gauge")
            if g is None:
                g = "none (component's own leads)" if v.get("ignore_in_bom") else "MISSING"
            fr, to = ends.get(k, [("?", "?")])[0]
            rows.append(dict(file=os.path.basename(f), id=k, gauge=g, n=v.get("wirecount"), col=", ".join(v.get("colors", [])),
                             fr=fr, to=to, what=v.get("notes", ""), bom="no" if v.get("ignore_in_bom") else "yes", com=C.get(k, "")))
    return rows


def to_markdown(rows):
    out = []
    out.append("# Wire list\n")
    out.append("All cables in `harness/*.yaml`, with gauge, what they connect and comments. Generated from the YAML files, so regenerate it after changing them.\n")
    out.append("- **From / To** are connector IDs as drawn in each harness; the pins used are in the YAML.")
    out.append("- **BOM**: `no` means the wire belongs to a component (motor leads, capacitor legs, UBEC leads), so it is not bought.")
    out.append("- **Length**: every length is still a placeholder (0) until the layout analysis is done.")
    out.append("- Gauges marked as placeholder are not decided yet; the others are recommendations written into the YAML comments.\n")
    out.append(f"Total: {len(rows)} cables.\n")
    cur = None
    for r in rows:
        if r["file"] != cur:
            cur = r["file"]
            out.append(f"\n## {cur}\n")
            out.append("| ID | Gauge | Wires (colours) | From | To | What it connects | BOM | Comments |")
            out.append("|---|---|---|---|---|---|---|---|")
        cm = r["com"].replace("|", "/")
        out.append(f"| {r['id']} | {r['gauge']} | {r['n']} ({r['col']}) | {r['fr']} | {r['to']} | {r['what']} | {r['bom']} | {cm} |")
    return "\n".join(out) + "\n"


def to_html(rows):
    files = []
    for r in rows:
        if r["file"] not in files:
            files.append(r["file"])
    body = ["<h1>Wire list</h1>",
            f"<p>All {len(rows)} cables in <code>harness/*.yaml</code>, with gauge, what they connect and comments. "
            "Generated from the YAML files.</p>",
            "<ul>",
            "<li><b>From / To</b> are connector IDs as drawn in each harness; the pins used are in the YAML.</li>",
            "<li><b>BOM</b>: <code>no</code> means the wire belongs to a component (motor leads, capacitor legs, UBEC leads), so it is not bought.</li>",
            "<li><b>Length</b>: every length is still a placeholder (0 m) until the layout analysis is done.</li>",
            "<li>Gauges marked as placeholder are not decided yet; the others are recommendations written into the YAML comments.</li>",
            "</ul>",
            '<ul class="toc">']
    for f in files:
        stem = f[:-5]
        body.append(f'<li><a href="#{esc(stem)}">{esc(f)}</a> '
                    f'(<a href="{esc(stem)}.html">diagram</a>)</li>')
    body.append("</ul>")
    for f in files:
        stem = f[:-5]
        body.append(f'<h2 id="{esc(stem)}">{esc(f)}</h2>')
        cells = []
        for r in (x for x in rows if x["file"] == f):
            cells.append([esc(r["id"]), esc(r["gauge"]), esc(f"{r['n']} ({r['col']})"), esc(r["fr"]), esc(r["to"]),
                          esc(r["what"]), esc(r["bom"]), esc(r["com"])])
        body.append(table(["ID", "Gauge", "Wires (colours)", "From", "To", "What it connects", "BOM", "Comments"],
                          cells, nowrap=(0,)))
    return page("Sage wire list", "\n".join(body))


rows = build_rows()
missing = [r["id"] for r in rows if not r["com"]]
print("rows", len(rows), "no comment:", missing, file=sys.stderr)

os.makedirs(os.path.join(root, "docs"), exist_ok=True)
os.makedirs(os.path.join(root, "build"), exist_ok=True)
open(os.path.join(root, "docs", "wire_list.md"), "w", encoding="utf-8", newline="\n").write(to_markdown(rows))
open(os.path.join(root, "build", "wire_list.html"), "w", encoding="utf-8", newline="\n").write(to_html(rows))
