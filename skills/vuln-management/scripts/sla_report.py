#!/usr/bin/env python3
"""Print SLA status, aging buckets and MTTR from a findings export.

Usage:
    python3 sla_report.py findings.csv
    python3 sla_report.py findings.json --as-of 2026-11-01
    python3 sla_report.py findings.csv --sla critical=7,high=30,medium=90,low=180

Input is a CSV with a header row, or JSON (a list of objects, or an object
with a "findings" or "results" list, as DefectDojo's API returns). Column
names are matched case-insensitively against common aliases:

    id          id, finding_id, key
    title       title, cve, vulnerability_id, rule
    severity    severity (critical, high, medium, low, info)
    first seen  first_seen, date, found, created, created_at
    closed      closed, mitigated, fixed_at, closed_at (empty if open)
    owner       owner, assignee, team
    exception   exception_expiry, risk_accepted_until, accepted_until

Dates are YYYY-MM-DD or ISO 8601. Python 3 standard library only.
Exit code is 1 when any open finding is past its SLA, so CI can gate on it.
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime

DEFAULT_SLA = {"critical": 7, "high": 30, "medium": 90, "low": 180}
SEVERITIES = ["critical", "high", "medium", "low", "info"]
BUCKETS = [(0, 30, "0-30"), (31, 60, "31-60"), (61, 90, "61-90"),
           (91, 180, "91-180"), (181, None, "180+")]
DUE_SOON_DAYS = 7

ALIASES = {
    "id": ["id", "finding_id", "key"],
    "title": ["title", "cve", "vulnerability_id", "rule"],
    "severity": ["severity"],
    "first_seen": ["first_seen", "date", "found", "created", "created_at"],
    "closed": ["closed", "mitigated", "fixed_at", "closed_at"],
    "owner": ["owner", "assignee", "team"],
    "exception": ["exception_expiry", "risk_accepted_until", "accepted_until"],
}


def parse_date(value):
    if value in (None, "", "null", "None"):
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        raise SystemExit(f"error: cannot parse date {text!r}")


def pick(row, field):
    lower = {str(k).lower(): v for k, v in row.items()}
    for name in ALIASES[field]:
        if name in lower and lower[name] not in (None, ""):
            return lower[name]
    return None


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        if path.lower().endswith(".json"):
            data = json.load(fh)
            if isinstance(data, dict):
                data = data.get("findings") or data.get("results") or []
            return data
        return list(csv.DictReader(fh))


def parse_sla(text):
    sla = dict(DEFAULT_SLA)
    if text:
        for part in text.split(","):
            sev, _, days = part.partition("=")
            sla[sev.strip().lower()] = int(days)
    return sla


def bucket(age):
    for low, high, label in BUCKETS:
        if age >= low and (high is None or age <= high):
            return label
    return BUCKETS[0][2]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path")
    ap.add_argument("--as-of", help="report date, default today")
    ap.add_argument("--sla", help="override days, e.g. critical=7,high=30")
    args = ap.parse_args()

    today = parse_date(args.as_of) if args.as_of else date.today()
    sla = parse_sla(args.sla)
    rows = load(args.path)

    open_rows, mttr = [], defaultdict(list)
    aging = defaultdict(lambda: defaultdict(int))
    status_count = defaultdict(int)

    for row in rows:
        sev = str(pick(row, "severity") or "info").strip().lower()
        first = parse_date(pick(row, "first_seen"))
        closed = parse_date(pick(row, "closed"))
        if first is None:
            print(f"warning: no first-seen date, skipped: {row}", file=sys.stderr)
            continue
        if closed:
            mttr[sev].append((closed - first).days)
            continue
        age = (today - first).days
        aging[sev][bucket(age)] += 1
        days = sla.get(sev)
        exc = parse_date(pick(row, "exception"))
        if exc and exc >= today:
            status = "excepted"
            left = (exc - today).days
        elif days is None:
            status, left = "no sla", None
        else:
            left = days - age
            if exc:
                status = "exception expired"
            elif left < 0:
                status = "breached"
            elif left <= DUE_SOON_DAYS:
                status = "due soon"
            else:
                status = "within sla"
        status_count[status] += 1
        open_rows.append((sev, age, left, status, row))

    print(f"# SLA report as of {today}\n")
    print("SLA days: " + ", ".join(f"{k} {v}" for k, v in sla.items()) + "\n")
    print("## Status of open findings\n")
    print("| Status | Count |\n|---|---|")
    for s in ["breached", "exception expired", "due soon", "within sla",
              "excepted", "no sla"]:
        if status_count[s]:
            print(f"| {s} | {status_count[s]} |")

    print("\n## Aging buckets (open, days since first seen)\n")
    labels = [b[2] for b in BUCKETS]
    print("| Severity | " + " | ".join(labels) + " |")
    print("|---" * (len(labels) + 1) + "|")
    for sev in SEVERITIES:
        if sev in aging:
            print(f"| {sev} | " + " | ".join(str(aging[sev][l]) for l in labels) + " |")

    print("\n## Breached and expiring (worst first)\n")
    flagged = [r for r in open_rows
               if r[3] in ("breached", "exception expired", "due soon")]
    flagged.sort(key=lambda r: (SEVERITIES.index(r[0]) if r[0] in SEVERITIES else 9,
                                r[2] if r[2] is not None else 0))
    if not flagged:
        print("None.")
    else:
        print("| Severity | ID | Title | Owner | Age | Days left | Status |")
        print("|---|---|---|---|---|---|---|")
        for sev, age, left, status, row in flagged:
            print(f"| {sev} | {pick(row, 'id') or '-'} | {pick(row, 'title') or '-'} "
                  f"| {pick(row, 'owner') or 'UNASSIGNED'} | {age} | {left} | {status} |")

    print("\n## MTTR (closed findings)\n")
    if not mttr:
        print("No closed findings in input.")
    else:
        print("| Severity | Closed | Mean days | Median days | Within SLA |")
        print("|---|---|---|---|---|")
        for sev in SEVERITIES:
            vals = sorted(mttr.get(sev, []))
            if not vals:
                continue
            mid = len(vals) // 2
            median = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
            limit = sla.get(sev)
            within = (f"{sum(v <= limit for v in vals)}/{len(vals)}"
                      if limit is not None else "-")
            print(f"| {sev} | {len(vals)} | {sum(vals) / len(vals):.1f} "
                  f"| {median} | {within} |")

    return 1 if status_count["breached"] or status_count["exception expired"] else 0


if __name__ == "__main__":
    sys.exit(main())
