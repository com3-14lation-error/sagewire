#!/usr/bin/env python3
"""Consolidated BOM of the whole aircraft, from the per-harness BOMs that WireViz writes.

    python scripts/make_bom.py [BUILD_FOLDER]

Run `python scripts/render.py` first: every `build/<harness>.bom.tsv` is read, lines with the same
description, unit, manufacturer and MPN are merged (quantities added, designators and harness
names listed), and the result is written to the build folder as

    bom.html   the page for GitHub Pages (parts, connectors and wire, with totals)
    bom.csv    the same lines as a flat file (opens in a spreadsheet)

Wire lengths are still placeholders (0 m) until the layout analysis, so the wire quantities are 0.
A warning is printed if a BOM file is older than its harness file (render again).

Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

from reports_html import esc, page, table

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = ("Parts", "Connectors", "Wire")
CATEGORY_TITLES = {
    "Parts": "Parts and modules",
    "Connectors": "Connectors",
    "Wire": "Wire (length in metres, placeholders until the layout analysis)",
}


def category(description: str) -> str:
    if description.startswith("Cable,"):
        return "Wire"
    if description.startswith("Connector,"):
        return "Connectors"
    return "Parts"


def read_boms(build: Path, harness: Path) -> tuple[list[dict], list[str]]:
    """Every BOM line of every harness, with the harness name; plus the stale-file warnings."""
    files = sorted(build.glob("*.bom.tsv"))
    if not files:
        raise SystemExit(f"make_bom: no *.bom.tsv in {build}: run `python scripts/render.py`")
    wanted = {y.stem for y in harness.glob("*.yaml")}
    have = {f.name[: -len(".bom.tsv")] for f in files}
    if wanted - have:
        raise SystemExit("make_bom: no BOM for " + ", ".join(sorted(wanted - have))
                         + ": run `python scripts/render.py`")
    if have - wanted:
        raise SystemExit("make_bom: BOM left over from a removed harness: "
                         + ", ".join(sorted(have - wanted)) + " (clear build/ and render again)")
    lines, stale = [], []
    for f in files:
        name = f.name[: -len(".bom.tsv")]
        if f.stat().st_mtime < (harness / f"{name}.yaml").stat().st_mtime:
            stale.append(name)
        with f.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                lines.append({
                    "harness": name,
                    "description": (row.get("Description") or "").strip(),
                    "qty": float(row.get("Qty") or 0),
                    "unit": (row.get("Unit") or "").strip(),
                    "designators": [d.strip() for d in (row.get("Designators") or "").split(",")
                                    if d.strip()],
                    "manufacturer": (row.get("Manufacturer") or "").strip(),
                    "mpn": (row.get("MPN") or "").strip(),
                })
    return lines, stale


def consolidate(lines: list[dict]) -> list[dict]:
    merged: dict[tuple, dict] = {}
    for ln in lines:
        key = (ln["description"], ln["unit"], ln["manufacturer"], ln["mpn"])
        item = merged.setdefault(key, {
            "category": category(ln["description"]), "description": ln["description"],
            "unit": ln["unit"], "manufacturer": ln["manufacturer"], "mpn": ln["mpn"],
            "qty": 0.0, "designators": [], "harnesses": [],
        })
        item["qty"] += ln["qty"]
        item["designators"] += ln["designators"]
        if ln["harness"] not in item["harnesses"]:
            item["harnesses"].append(ln["harness"])
    items = list(merged.values())
    for it in items:
        it["designators"] = sorted(set(it["designators"]))
        it["harnesses"].sort()
    order = {c: i for i, c in enumerate(CATEGORIES)}
    items.sort(key=lambda it: (order[it["category"]], it["description"].lower()))
    for n, it in enumerate(items, 1):
        it["id"] = n
    return items


def fmt_qty(qty: float) -> str:
    return str(int(qty)) if float(qty).is_integer() else f"{qty:.3f}".rstrip("0").rstrip(".")


def to_csv(items: list[dict]) -> str:
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["Id", "Category", "Description", "Qty", "Unit", "Manufacturer", "MPN",
                "Designators", "Harnesses"])
    for it in items:
        w.writerow([it["id"], it["category"], it["description"], fmt_qty(it["qty"]), it["unit"],
                    it["manufacturer"], it["mpn"], ", ".join(it["designators"]),
                    ", ".join(it["harnesses"])])
    return out.getvalue()


def to_html(items: list[dict]) -> str:
    counts = {c: sum(1 for it in items if it["category"] == c) for c in CATEGORIES}
    no_mpn = sum(1 for it in items if it["category"] != "Wire" and not it["mpn"])
    body = ["<h1>Consolidated BOM</h1>",
            "<p>Every harness BOM merged: lines with the same description, manufacturer and MPN "
            "are added together. The per-harness lists are the BOM tables on each harness page. "
            '<a href="bom.csv">Download as CSV</a>.</p>',
            f'<p class="muted">{counts["Parts"]} part lines, {counts["Connectors"]} connector '
            f'lines, {counts["Wire"]} wire lines. <span class="warn">{no_mpn} part and connector '
            "lines have no MPN yet</span> (series-only or not chosen); wire lengths are all "
            "placeholders (0 m).</p>"]
    for cat in CATEGORIES:
        rows = []
        for it in (i for i in items if i["category"] == cat):
            qty = fmt_qty(it["qty"]) + (f' {esc(it["unit"])}' if it["unit"] else "")
            mpn = esc(it["mpn"]) if it["mpn"] else (
                "" if cat == "Wire" else '<span class="warn">&mdash;</span>')
            rows.append([str(it["id"]), esc(it["description"]), qty, esc(it["manufacturer"]), mpn,
                         esc(", ".join(it["designators"])),
                         esc(", ".join(h.removesuffix("_system") for h in it["harnesses"]))])
        body.append(f"<h2>{esc(CATEGORY_TITLES[cat])}</h2>")
        body.append(table(["Id", "Description", "Qty", "Manufacturer", "MPN", "Designators",
                           "Harnesses"], rows, numeric=(0, 2)))
    return page("Sage consolidated BOM", "\n".join(body))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Consolidated BOM from build/*.bom.tsv.")
    p.add_argument("build", nargs="?", type=Path, help="build folder (default: build)")
    args = p.parse_args(argv)
    build = args.build or ROOT / "build"
    lines, stale = read_boms(build, ROOT / "harness")
    if stale:
        print("warning: older than their harness file, render again? " + ", ".join(stale),
              file=sys.stderr)
    items = consolidate(lines)
    (build / "bom.html").write_text(to_html(items), encoding="utf-8", newline="\n")
    (build / "bom.csv").write_text(to_csv(items), encoding="utf-8", newline="\n")
    print(f"{len(items)} BOM lines from {len(lines)} harness lines -> "
          f"{build / 'bom.html'} and {build / 'bom.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
