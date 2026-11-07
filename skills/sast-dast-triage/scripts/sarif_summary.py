#!/usr/bin/env python3
"""Summarize one or more SARIF files by rule, severity and file.

Usage:
    python3 sarif_summary.py results.sarif [more.sarif ...]
    python3 sarif_summary.py --by-file results.sarif

Prints a markdown table sorted by security severity (highest first), then
by count. Python 3 standard library only.
"""

import json
import sys
from collections import defaultdict

LEVEL_SCORE = {"error": 7.0, "warning": 4.0, "note": 1.0, "none": 0.0}


def rule_index(run):
    rules = {}
    driver = run.get("tool", {}).get("driver", {})
    tool = driver.get("name", "unknown")
    for ext in [driver] + run.get("tool", {}).get("extensions", []):
        for r in ext.get("rules", []) or []:
            rules[r.get("id")] = r
    return tool, rules


def severity(result, rule):
    props = (rule or {}).get("properties", {}) or {}
    sev = props.get("security-severity")
    if sev is not None:
        try:
            return float(sev)
        except (TypeError, ValueError):
            pass
    level = result.get("level") or (rule or {}).get("defaultConfiguration", {}).get("level", "warning")
    return LEVEL_SCORE.get(level, 4.0)


def location(result):
    locs = result.get("locations") or []
    if not locs:
        return "?", 0
    phys = locs[0].get("physicalLocation", {})
    uri = phys.get("artifactLocation", {}).get("uri", "?")
    line = phys.get("region", {}).get("startLine", 0)
    return uri, line


def main(argv):
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    by_file = False
    if argv and argv[0] == "--by-file":
        by_file = True
        argv = argv[1:]
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    groups = defaultdict(lambda: {"count": 0, "sev": 0.0, "files": set()})
    total = 0
    for path in argv:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        for run in data.get("runs", []):
            tool, rules = rule_index(run)
            for res in run.get("results", []):
                rid = res.get("ruleId") or res.get("rule", {}).get("id", "?")
                uri, line = location(res)
                key = (tool, rid, uri) if by_file else (tool, rid)
                g = groups[key]
                g["count"] += 1
                g["sev"] = max(g["sev"], severity(res, rules.get(rid)))
                g["files"].add(f"{uri}:{line}")
                total += 1

    rows = sorted(groups.items(), key=lambda kv: (-kv[1]["sev"], -kv[1]["count"]))
    print(f"Total results: {total}, groups: {len(rows)}\n")
    if by_file:
        print("| Severity | Tool | Rule | File | Count | Lines |")
        print("|---|---|---|---|---|---|")
    else:
        print("| Severity | Tool | Rule | Count | Example locations |")
        print("|---|---|---|---|---|")
    for key, g in rows:
        sample = ", ".join(sorted(g["files"])[:3])
        if by_file:
            tool, rid, uri = key
            lines = ", ".join(f.rsplit(":", 1)[1] for f in sorted(g["files"])[:10])
            print(f"| {g['sev']:.1f} | {tool} | {rid} | {uri} | {g['count']} | {lines} |")
        else:
            tool, rid = key
            print(f"| {g['sev']:.1f} | {tool} | {rid} | {g['count']} | {sample} |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
