#!/usr/bin/env python3
"""Audit Awesome-Ollama entries for maintenance problems.

Checks every entry with a GitHub repo link via the GitHub API:
  - dead repo (404)
  - archived repo
  - no push in >365 days (or >STALE_DAYS env)
  - README license column no longer matches the repo license

OSS entries must link to a repo (that rule itself is lint.py's job).
Runs green (exit 0) even with findings - this is advisory, run monthly via CI.

Usage:
  GH_TOKEN=... python scripts/audit.py README.md > report.md
"""
import json
import os
import re
import sys
import time
import urllib.request

STALE_DAYS = int(os.environ.get("STALE_DAYS", "365"))
API = "https://api.github.com"


def gh(path):
    req = urllib.request.Request(f"{API}{path}", headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "awesome-ollama-audit",
    })
    token = os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception:
        return None


def parse_rows(path):
    for line in open(path, encoding="utf-8"):
        s = line.rstrip("\n")
        if not s.startswith("|") or "Name/Link" in s or "---" in s:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) != 4:
            continue
        link = (re.search(r"\((https?://[^)]+)\)", cells[0]) or [None, ""])[1]
        yield {"name": re.sub(r"\[|\]\([^)]*\)", "", cells[0]).strip(),
               "link": link, "license": cells[3]}


def main(path):
    now = time.time()
    findings = []
    rows = list(parse_rows(path))
    for r in rows:
        m = re.match(r"https://(www\.)?github\.com/([\w.-]+)/([\w.-]+)", r["link"])
        if not m:
            if r["license"] in ("MIT", "Apache-2.0", "GPL-3.0", "GPL-2.0", "AGPL-3.0"):
                findings.append(f"- **{r['name']}**: OSS license `{r['license']}` but no repo link: {r['link']}")
            continue
        repo = f"{m.group(2)}/{m.group(3)}"
        d = gh(f"/repos/{repo}")
        if d is None:
            findings.append(f"- **{r['name']}**: repo {repo} unreachable/404")
            continue
        if d.get("archived"):
            findings.append(f"- **{r['name']}**: repo {repo} is ARCHIVED")
        pushed = d.get("pushed_at") or ""
        if pushed:
            age_days = int((now - time.mktime(time.strptime(pushed[:10], "%Y-%m-%d"))) / 86400)
            if age_days > STALE_DAYS:
                findings.append(f"- **{r['name']}**: no push in {age_days} days ({repo})")
        spdx = (d.get("license") or {}).get("spdx_id")
        # ponytail: mismatch check ignores custom licenses - GitHub detection
        # is unreliable on modified MIT/Apache files (Open WebUI, Dify, ...)
        if spdx and spdx != "NOASSERTION" and r["license"] not in (spdx, "Custom", "Proprietary"):
            findings.append(f"- **{r['name']}**: README says {r['license']}, repo says {spdx} ({repo})")
        time.sleep(0.1)  # stay well under rate limits

    print("# Maintenance audit\n")
    if findings:
        print(f"{len(findings)} finding(s):\n")
        print("\n".join(findings))
    else:
        print("All entries healthy: repos live, pushed within "
              f"{STALE_DAYS} days, licenses match.")
    print(f"\n*{len(rows)} entries audited.*")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "README.md"))