"""Small shared helpers for the HTML report pages (consolidated BOM, wire list).

Standard library only. The pages are plain, self-contained HTML (no external files) with a light
and a dark colour scheme, so they work as GitHub Pages files next to the harness renders.
"""
from __future__ import annotations

import html
from collections.abc import Sequence

CSS = """
:root{color-scheme:light dark;--fg:#1a1a1a;--bg:#fff;--muted:#666;--line:#d0d0d0;--head:#f0f0f0;--warn:#a15c00}
@media (prefers-color-scheme:dark){:root{--fg:#e8e8e8;--bg:#161616;--muted:#a0a0a0;--line:#3a3a3a;--head:#242424;--warn:#e0a040}}
body{font:15px/1.45 system-ui,sans-serif;margin:1.5rem auto;padding:0 1rem;max-width:96rem;color:var(--fg);background:var(--bg)}
h1{font-size:1.5rem;margin:.2rem 0 .6rem}h2{font-size:1.15rem;margin:1.6rem 0 .5rem}
a{color:inherit}nav{margin-bottom:.8rem;font-size:.9rem}small,.muted{color:var(--muted)}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{border:1px solid var(--line);padding:.3rem .5rem;text-align:left;vertical-align:top}
th{background:var(--head);position:sticky;top:0}
td.num{text-align:right;white-space:nowrap}td.nowrap{white-space:nowrap}
.warn{color:var(--warn)}ul.toc{columns:2;padding-left:1.2rem}
""".strip()


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def page(title: str, body: str) -> str:
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
        f"<title>{esc(title)}</title>\n<style>\n{CSS}\n</style>\n</head>\n<body>\n"
        '<nav><a href="index.html">&larr; Sage wiring</a></nav>\n'
        f"{body}\n</body>\n</html>\n")


def table(headers: Sequence[str], rows: Sequence[Sequence[str]], numeric: Sequence[int] = (),
          nowrap: Sequence[int] = ()) -> str:
    """A table; cell strings are already-escaped HTML. `numeric` and `nowrap` are column indexes."""
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    out = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cls = "num" if i in numeric else ("nowrap" if i in nowrap else "")
            cells.append(f'<td class="{cls}">{cell}</td>' if cls else f"<td>{cell}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<div class="table-wrap"><table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n'
            + "\n".join(out) + "\n</tbody>\n</table></div>")
