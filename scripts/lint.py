#!/usr/bin/env python3
"""Lint README.md against the Awesome-Ollama table schema.

Usage:
  python scripts/lint.py README.md            # check (exit 1 on any issue)
  python scripts/lint.py README.md --fix     # also re-pad tables

ponytail: single-file, stdlib only. If this grows per-section rules,
split into a package then - not before.
"""
import re
import sys

INSTALL_ENUM = {
    "npm", "pip", "Docker", "Download", "Homebrew", "Browser extension",
    "Marketplace", "Maven", "pub", "NuGet", "CocoaPods", "Cargo", "Source",
}
LICENSE_ENUM = {
    "MIT", "Apache-2.0", "GPL-3.0", "GPL-2.0", "AGPL-3.0", "BSD-3-Clause",
    "MPL-2.0", "ISC", "Unlicense", "Custom", "Proprietary",
}
BANNED = [":heavy_check_mark:", "✔", "<br", "&nbsp;"]


def parse(text):
    """yield (lineno, section, cells) for every table row (incl. header/sep)."""
    section = None
    for i, line in enumerate(text.split("\n"), 1):
        s = line.rstrip()
        m = re.match(r"^##\s+(.*)", s)
        if m:
            section = m.group(1).strip()
        if s.startswith("|"):
            yield i, section, s


def split_row(s):
    return [c.strip() for c in s.strip("|").split("|")]


def lint(path, fix=False):
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    errors, warnings = [], []
    sections = {}  # section -> {'header':..., 'rows':[...], 'lines':[...]}
    cur = None

    for lineno, section, s in parse(text):
        cells = split_row(s)
        if re.match(r"^\|\s*-{2,}", s):
            cur["lines"].append((lineno, s, "sep"))
            continue
        if cells[0] == "Name/Link":
            if cells != ["Name/Link", "Description", "Install", "License"]:
                errors.append(f"L{lineno}: table header must be 'Name/Link | Description | Install | License', got {cells}")
            cur = sections.setdefault(section, {"rows": [], "lines": []})
            cur["lines"].append((lineno, s, "header"))
            continue
        if len(cells) != 4:
            errors.append(f"L{lineno}: row must have exactly 4 cells, got {len(cells)}: {s[:60]}...")
            continue
        cur["rows"].append((lineno, cells))
        cur["lines"].append((lineno, s, "row"))

        lineno_err = errors.append
        name, desc, install, license = cells
        if not re.fullmatch(r"\[[^\]]+\]\(https?://[^)]+\)", name):
            errors.append(f"L{lineno}: name cell must be a single markdown link: {name[:50]}")
        link = (re.search(r"\((https?://[^)]+)\)", name) or [None, ""])[1]
        if license not in ("Proprietary", "Custom") and not re.match(r"https://(www\.)?(github|gitlab)\.com/", link):
            errors.append(f"L{lineno}: OSS entry must link to its repo (github/gitlab), got {link[:50]}")
        if license not in LICENSE_ENUM:
            errors.append(f"L{lineno}: license '{license}' not in enum {sorted(LICENSE_ENUM)}")
        for v in [x.strip() for x in install.split(",")]:
            if v not in INSTALL_ENUM:
                errors.append(f"L{lineno}: install '{v}' not in enum {sorted(INSTALL_ENUM)}")
        if not desc.strip():
            errors.append(f"L{lineno}: empty description")
        for b in BANNED:
            if b in s:
                errors.append(f"L{lineno}: banned token '{b}'")
        if "  " in f"{desc} {install}":
            warnings.append(f"L{lineno}: double space in row")

    # padding consistency per section + ToC coverage
    for section, data in sections.items():
        widths = [max(len(split_row(s)[i]) for _, s, _ in data["lines"]) for i in range(4)]
        for lineno, s, kind in data["lines"]:
            cells = split_row(s)
            if kind == "sep":
                expected = "|" + "|".join(" " + "-" * w + " " for w in widths) + "|"
                if s != expected:
                    if fix:
                        lines[lineno - 1] = expected
                    else:
                        errors.append(f"L{lineno}: separator row not padded to match table (expected {len(expected)} chars)")
                continue
            expected = "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"
            if s != expected:
                if fix:
                    lines[lineno - 1] = expected
                else:
                    errors.append(f"L{lineno}: cell padding inconsistent with column width (run with --fix)")

    toc = re.findall(r"^\s*-\s*\[([^\]]+)\]", text, re.M)
    toc_sections = [t for t in toc if t != "Awesome Ollama"]
    have = list(sections)
    if toc_sections != have:
        errors.append(f"ToC mismatch: ToC has {toc_sections}, README sections are {have}")

    if fix:
        open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    for e in errors:
        print(f"ERROR: {e}")
    for w in warnings:
        print(f"WARN:  {w}")
    print(f"{len(sections)} sections, {sum(len(d['rows']) for d in sections.values())} entries, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: lint.py README.md [--fix]")
    sys.exit(lint(sys.argv[1], "--fix" in sys.argv))