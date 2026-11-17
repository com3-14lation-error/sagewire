#!/usr/bin/env python3
"""Publish the rendered harnesses as a GitHub Pages branch (default `gh-pages`).

    python scripts/publish_pages.py [BUILD_FOLDER] [--push] [--dry-run]

Run `python scripts/render.py`, then `python scripts/make_bom.py` and
`.venv/Scripts/python scripts/make_wire_list.py` first (clear build/ beforehand for a clean set).
The branch holds one commit per publication, each a snapshot of: every harness `*.html` in the
build folder, the reports (`bom.html`, `bom.csv`, `wire_list.html`), an `index.html` that lists
the reports first and then the harness pages by file name, and a `.nojekyll`. The first commit has no parent;
later ones sit on top of the previous tip, so the push is always a fast-forward and nothing is
ever force-pushed. Nothing is pushed unless `--push` is given; GitHub Pages itself is switched
on by hand (Settings, Pages, branch, root).

Checks before anything is committed: every harness/*.yaml has its page and no page is left over
from a harness that no longer exists; every relative link in the pages points at a file on the
branch; the tracked files are committed (the page says which commit it was built from).

Standard library only. The branch is built with git plumbing and a temporary index, so the
working tree and the checked-out branch are never touched.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from html.parser import HTMLParser
from pathlib import Path

INDEX = "index.html"
# Reports written by make_bom.py and make_wire_list.py: (file, title shown on the index page).
REPORTS = (
    ("bom.html", "Bill of materials (all harnesses)"),
    ("wire_list.html", "Wire list"),
    ("bom.csv", "Bill of materials as CSV"),
)
REPORT_NAMES = tuple(n for n, _ in REPORTS)
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.IGNORECASE)  # http:, data:, mailto:, //host


class PublishError(Exception):
    """Something that must stop the publication; the message says what to do."""


def git(repo: Path, *args: str, env: dict[str, str] | None = None, check: bool = True) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
        env={**os.environ, **(env or {})}, check=False,
    )
    if check and done.returncode != 0:
        why = done.stderr.strip() or done.stdout.strip()
        raise PublishError(f"git {' '.join(args)} failed: {why}")
    return done.stdout.strip()


# ------------------------------------------------------------------------------------ link check
class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if value and key in ("href", "src", "poster", "data") and tag in (
                    "a", "link", "img", "script", "source", "video", "object", "iframe"):
                self.urls.append(value)


def relative_links(page: str) -> list[str]:
    """The files a page links to by relative path (no `#fragment`, no query, no external URL)."""
    parser = _Links()
    parser.feed(page)
    out = []
    for url in parser.urls:
        if url.startswith("#") or EXTERNAL.match(url):
            continue
        path = re.split(r"[?#]", url, maxsplit=1)[0]
        if path:
            out.append(path)
    return sorted(set(out))


# ------------------------------------------------------------------------------------- the pages
def collect(build: Path, harness: Path) -> list[str]:
    """The page names to publish: every *.html in the build folder, checked against the harnesses."""
    if not build.is_dir():
        raise PublishError(f"{build} not found: run `python scripts/render.py`")
    pages = sorted(p.name for p in build.glob("*.html")
                   if p.name != INDEX and p.name not in REPORT_NAMES)
    wanted = {f"{y.stem}.html" for y in harness.glob("*.yaml")}
    missing = sorted(wanted - set(pages))
    extra = sorted(set(pages) - wanted)
    problems = [f"{n}: no page (run `python scripts/render.py`)" for n in missing]
    problems += [f"{n}: no harness/{n[:-5]}.yaml any more (clear build/ and render again)"
                 for n in extra]
    if problems:
        raise PublishError("build/ does not match harness/:\n  " + "\n  ".join(problems))
    if not pages:
        raise PublishError(f"no harness pages in {build}")
    missing_reports = [n for n in REPORT_NAMES if not (build / n).is_file()]
    if missing_reports:
        raise PublishError(
            "reports missing from build/: " + ", ".join(missing_reports)
            + " (run `python scripts/make_bom.py` and "
            "`.venv/Scripts/python scripts/make_wire_list.py`)")
    return pages


def stale(build: Path, harness: Path, pages: Sequence[str]) -> list[str]:
    """Pages older than their harness file, reports older than the newest harness file."""
    out = [n for n in pages
           if (build / n).stat().st_mtime < (harness / f"{n[:-5]}.yaml").stat().st_mtime]
    newest = max((y.stat().st_mtime for y in harness.glob("*.yaml")), default=0)
    out += [n for n in REPORT_NAMES if (build / n).stat().st_mtime < newest]
    return out


def index_page(pages: Sequence[str], commit: str, date: str) -> str:
    reports = "\n".join(f'    <li><a href="{html.escape(n)}">{html.escape(t)}</a></li>'
                        for n, t in REPORTS)
    items = "\n".join(f'    <li><a href="{html.escape(n)}">{html.escape(n)}</a></li>'
                      for n in pages)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="color-scheme" content="light dark">\n'
        "<title>Sage wiring</title>\n"
        "<style>body{font:16px/1.5 system-ui,sans-serif;max-width:40rem;margin:2rem auto;"
        "padding:0 1rem}h2{font-size:1.1rem;margin:1.5rem 0 .5rem}li{margin:.25rem 0}"
        "small{opacity:.7}</style>\n"
        "</head>\n<body>\n"
        "<h1>Sage wiring</h1>\n"
        f"<ul>\n{reports}\n</ul>\n"
        "<h2>Harnesses</h2>\n"
        f"<ul>\n{items}\n</ul>\n"
        f"<p><small>Built from commit {html.escape(commit)}, {html.escape(date)}.</small></p>\n"
        "</body>\n</html>\n")


# -------------------------------------------------------------------------------------- the branch
def stage(build: Path, pages: Sequence[str], commit: str, date: str, dest: Path) -> list[str]:
    """Copy the pages into `dest` byte for byte, add index.html and .nojekyll; return all names."""
    for name in (*pages, *REPORT_NAMES):
        (dest / name).write_bytes((build / name).read_bytes())
    (dest / INDEX).write_text(index_page(pages, commit, date), encoding="utf-8", newline="\n")
    (dest / ".nojekyll").write_text("", encoding="utf-8")
    return sorted({*pages, *REPORT_NAMES, INDEX, ".nojekyll"})


def missing_links(staging: Path, files: Sequence[str]) -> list[str]:
    have = set(files)
    gone = []
    for name in files:
        if not name.endswith(".html"):
            continue
        page = (staging / name).read_text(encoding="utf-8", errors="replace")
        gone += [f"{name} -> {u}" for u in relative_links(page) if u.removeprefix("./") not in have]
    return gone


def tip(repo: Path, branch: str, remote: str, fetch: bool) -> str:
    """The commit to build on: the local branch, else the remote's (fetched), else none."""
    local = git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
    if local:
        return local
    remote_ref = f"refs/remotes/{remote}/{branch}"
    if fetch and git(repo, "ls-remote", "--heads", remote, branch, check=False):
        git(repo, "fetch", remote, f"refs/heads/{branch}:{remote_ref}")
    return git(repo, "rev-parse", "--verify", "--quiet", remote_ref, check=False)


def commit_snapshot(repo: Path, staging: Path, parent: str, message: str) -> tuple[str, str]:
    """A commit of `staging` (on `parent` if given), via a temporary index; returns (commit, tree)."""
    with tempfile.TemporaryDirectory() as tmp:
        env = {"GIT_INDEX_FILE": str(Path(tmp) / "index"), "GIT_WORK_TREE": str(staging)}
        git(repo, "-c", "core.autocrlf=false", "add", "--force", "--all", env=env)
        tree = git(repo, "write-tree", env=env)
    if parent and git(repo, "rev-parse", f"{parent}^{{tree}}") == tree:
        return "", tree
    args = ["commit-tree", tree, "-m", message] + (["-p", parent] if parent else [])
    return git(repo, *args), tree


def pages_url(repo: Path, remote: str) -> str:
    url = git(repo, "remote", "get-url", remote, check=False)
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$", url)
    return f"https://{m.group(1).lower()}.github.io/{m.group(2)}/" if m else ""


def publish(
    build: Path, repo: Path, *, branch: str = "gh-pages", remote: str = "origin",
    push: bool = False, dry_run: bool = False, allow_dirty: bool = False,
) -> dict[str, str]:
    if git(repo, "symbolic-ref", "--short", "-q", "HEAD", check=False) == branch:
        raise PublishError(f"{branch} is the checked-out branch: switch to another one first")
    if git(repo, "status", "--porcelain", "--untracked-files=no") and not allow_dirty:
        raise PublishError("tracked files have uncommitted changes, so the page could not be "
                           "traced to a commit: commit them, or pass --allow-dirty")
    pages = collect(build, repo / "harness")
    commit = git(repo, "rev-parse", "--short", "HEAD")
    date = git(repo, "show", "-s", "--format=%cs", "HEAD")
    parent = tip(repo, branch, remote, fetch=not dry_run)
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)
        files = stage(build, pages, commit, date, staging)
        gone = missing_links(staging, files)
        if gone:
            raise PublishError("links to files that would not be on the branch (they would "
                               "404):\n  " + "\n  ".join(gone))
        info = {"branch": branch, "files": str(len(files)), "commit": "",
                "stale": ", ".join(stale(build, repo / "harness", pages))}
        if dry_run:
            info["parent"] = parent
            return info
        new, _ = commit_snapshot(repo, staging, parent, f"pages: harness renders and reports of {commit}")
    if not new:
        info["unchanged"] = "yes"
        return info
    info["commit"] = new
    git(repo, "update-ref", f"refs/heads/{branch}", new)
    if push:
        git(repo, "push", remote, f"refs/heads/{branch}:refs/heads/{branch}")
        info["pushed"] = remote
    info["pages"] = pages_url(repo, remote)
    return info


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Publish build/*.html as the GitHub Pages branch.")
    p.add_argument("build", nargs="?", type=Path, help="folder of rendered pages (default: build)")
    p.add_argument("--repo", type=Path, default=None, help="the git clone (default: this one)")
    p.add_argument("--branch", default="gh-pages", help="branch to publish to (default: gh-pages)")
    p.add_argument("--remote", default="origin")
    p.add_argument("--push", action="store_true", help="push the branch (fast-forward only)")
    p.add_argument("--dry-run", action="store_true",
                   help="run every check and say what would be published; create nothing")
    p.add_argument("--allow-dirty", action="store_true",
                   help="publish with uncommitted changes to tracked files")
    args = p.parse_args(argv)
    try:
        repo = args.repo or Path(git(Path(__file__).resolve().parent, "rev-parse",
                                     "--show-toplevel"))
        info = publish(args.build or repo / "build", repo, branch=args.branch,
                       remote=args.remote, push=args.push, dry_run=args.dry_run,
                       allow_dirty=args.allow_dirty)
    except (PublishError, OSError) as exc:
        print(f"publish_pages: {exc}", file=sys.stderr)
        return 1
    if info["stale"]:
        print(f"warning: older than their harness file, render again? {info['stale']}",
              file=sys.stderr)
    if args.dry_run:
        print(f"dry run: would add a commit to {info['branch']} with {info['files']} files "
              f"({'on ' + info['parent'][:10] if info['parent'] else 'first commit'}); "
              "every link resolves; nothing was created")
        return 0
    if info.get("unchanged"):
        print(f"{info['branch']} already holds exactly these pages; nothing to do")
        return 0
    print(f"committed {info['branch']} ({info['commit'][:10]}): {info['files']} files")
    if "pushed" in info:
        print(f"pushed to {info['pushed']}")
    else:
        print(f"not pushed: git push {args.remote} {info['branch']}  (or use --push next time)")
    print(f"to serve it: Settings, Pages, branch {info['branch']}, folder /"
          + (f"  ->  {info['pages']}" if info.get("pages") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
