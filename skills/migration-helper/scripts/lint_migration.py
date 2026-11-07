#!/usr/bin/env python3
"""Flag risky statements in SQL migration files.

Usage:
    python3 lint_migration.py path/to/migration.sql [more.sql ...]
    alembic upgrade head --sql | python3 lint_migration.py -

Checks are heuristics for Postgres and MySQL. A clean run does not mean
the migration is safe. Exit code is 1 if any high severity issue is found.
"""
import re
import sys

RULES = [
    ("high", r"\bCREATE\s+(UNIQUE\s+)?INDEX\b(?!\s+CONCURRENTLY)",
     "CREATE INDEX without CONCURRENTLY blocks writes (Postgres)"),
    ("high", r"\bDROP\s+INDEX\b(?!\s+CONCURRENTLY)",
     "DROP INDEX without CONCURRENTLY takes ACCESS EXCLUSIVE (Postgres)"),
    ("high", r"\bALTER\s+COLUMN\s+\S+\s+(SET\s+DATA\s+)?TYPE\b",
     "column type change usually rewrites the table"),
    ("high", r"\bMODIFY\s+COLUMN\b",
     "MODIFY COLUMN often uses ALGORITHM=COPY (MySQL)"),
    ("high", r"\bSET\s+NOT\s+NULL\b",
     "SET NOT NULL scans the table under ACCESS EXCLUSIVE; add a valid CHECK first"),
    ("high", r"\bFOREIGN\s+KEY\b(?![^;]*\bNOT\s+VALID\b)",
     "foreign key without NOT VALID locks both tables while it validates"),
    ("medium", r"\bRENAME\s+(COLUMN|TO)\b",
     "rename breaks code that still uses the old name; use expand and contract"),
    ("medium", r"\bDROP\s+(COLUMN|TABLE)\b",
     "destructive: confirm no code reads it and a backup exists"),
    ("medium", r"\bTRUNCATE\b", "destructive: confirm a backup exists"),
    ("medium", r"\bUPDATE\s+\S+\s+SET\b(?![^;]*\bWHERE\b)",
     "UPDATE without WHERE touches every row in one transaction; batch it"),
    ("low", r"\bADD\s+COLUMN\b[^;]*\bDEFAULT\s+(now|current_timestamp|gen_random_uuid|uuid_generate)",
     "volatile default rewrites the table; add nullable and backfill"),
]

TIMEOUT = re.compile(r"\b(lock_timeout|lock_wait_timeout)\b", re.I)
DDL = re.compile(r"\b(ALTER|CREATE|DROP)\s+(TABLE|INDEX)\b", re.I)


def lint(name, text):
    findings = []
    for sev, pattern, msg in RULES:
        for m in re.finditer(pattern, text, re.I | re.S):
            line = text.count("\n", 0, m.start()) + 1
            findings.append((sev, name, line, msg))
    if DDL.search(text) and not TIMEOUT.search(text):
        findings.append(("medium", name, 1, "DDL without lock_timeout / lock_wait_timeout"))
    return findings


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    all_findings = []
    for path in argv[1:]:
        if path == "-":
            all_findings += lint("<stdin>", sys.stdin.read())
        else:
            with open(path, encoding="utf-8") as fh:
                all_findings += lint(path, fh.read())
    order = {"high": 0, "medium": 1, "low": 2}
    all_findings.sort(key=lambda f: (order[f[0]], f[1], f[2]))
    if not all_findings:
        print("no issues found")
        return 0
    print("| Severity | File | Line | Issue |")
    print("|---|---|---|---|")
    for sev, name, line, msg in all_findings:
        print(f"| {sev} | {name} | {line} | {msg} |")
    return 1 if any(f[0] == "high" for f in all_findings) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
