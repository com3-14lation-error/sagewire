"""Render the WireViz harnesses to build/.

Usage (from anywhere):
    python scripts/render.py                 render every harness/*.yaml and harness/alternatives/*.yaml
    python scripts/render.py power rf        render only some (name, name_system or file name)
    python scripts/render.py --open power    render, then open the PNG (Windows, macOS, Linux)

Output goes to build/ (git-ignored): <name>.png, .svg, .html and .tsv (the BOM). The alternatives
(harness/alternatives/) go to build/alternatives/, so the consolidated BOM does not see them.
Needs Graphviz on the PATH. Uses the wireviz in .venv if there is one, else the one on the PATH.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
ALTERNATIVES = HARNESS / "alternatives"
BUILD = ROOT / "build"


def find_wireviz():
    for rel in (".venv/Scripts/wireviz.exe", ".venv/bin/wireviz"):
        p = ROOT / rel
        if p.exists():
            return str(p)
    return shutil.which("wireviz")


def pick_files(names):
    files = sorted(HARNESS.glob("*.yaml")) + sorted(ALTERNATIVES.glob("*.yaml"))
    if not names:
        return files
    chosen = []
    for n in names:
        stem = Path(n).stem
        candidates = (stem, stem + "_system")
        match = [f for f in files if f.stem in candidates]
        if not match:
            sys.exit(f"No harness matches '{n}'. Available: " + ", ".join(f.stem for f in files))
        chosen.extend(match)
    return chosen


def open_file(path):
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="harnesses to render (default: all)")
    ap.add_argument("--open", action="store_true", help="open the PNG after rendering")
    args = ap.parse_args()

    wireviz = find_wireviz()
    if not wireviz:
        sys.exit("wireviz not found. Activate the venv or run: pip install -r requirements.txt")
    if not shutil.which("dot"):
        sys.exit("Graphviz ('dot') not found on the PATH. Install Graphviz first.")

    BUILD.mkdir(exist_ok=True)
    failed = []
    for f in pick_files(args.names):
        out = BUILD / "alternatives" if f.parent == ALTERNATIVES else BUILD
        out.mkdir(exist_ok=True)
        print(f"== {f.relative_to(HARNESS)}")
        r = subprocess.run([wireviz, "-f", "hpst", "-o", str(out), str(f)])
        if r.returncode != 0:
            failed.append(f.name)
        elif args.open:
            open_file(str(out / (f.stem + ".png")))

    if failed:
        sys.exit("Failed: " + ", ".join(failed))
    print(f"\nDone. Output in {BUILD}")


if __name__ == "__main__":
    main()
