---
name: vuln-management
description: Run a vulnerability management program across scanners over time. Set remediation SLAs by severity, prioritize with CVSS, EPSS, CISA KEV, reachability and exposure, dedupe findings from Trivy, Snyk, Dependabot, Semgrep and CodeQL, assign owners, track exceptions with expiry, and report aging, SLA breaches and MTTR in DefectDojo, Jira or GitHub issues. Use when the user asks about vuln SLAs, a remediation backlog, risk acceptance, merging findings from several scanners, or a monthly vulnerability report.
---

# Vulnerability Management

Scanners find issues. A program decides who fixes what by when, and proves it happened. This skill sets up and runs that loop: one system of record, one priority model, SLAs that mean something, and a report leadership can read in two minutes.

## When to use

- The team has findings from several scanners and no single list of what is open.
- Someone asks "what is our SLA for a critical?" or "how many highs are past due?"
- A backlog of hundreds of CVEs needs a fix order that is not just CVSS descending.
- An owner wants to accept a risk or delay a fix and needs an exception process.
- A monthly or quarterly report is due: open counts, aging, SLA breaches, MTTR.
- The user is setting up DefectDojo, or a Jira or GitHub issues workflow, for security findings.

Not for: deciding whether findings from one scan are real or false positives (use `sast-dast-triage`), reviewing a specific CVE, upgrade path, license or SBOM (use `dependency-supply-chain`), or an active exploitation or breach in progress (use `incident-response`).

## Steps

1. Pick the system of record. Every finding lives in exactly one place with a stable ID, owner, severity, first-seen date and status.
   - DefectDojo: import each scanner with its parser (`Trivy Scan`, `Snyk Scan`, `Dependabot Scan`, `SARIF`), one engagement per pipeline, reimport on each run so closed findings close themselves.
   - Jira or GitHub issues: one issue per deduped finding, labels for severity and scanner, a custom field or label for due date. Sync with a script or the scanner's integration, never by hand.
2. Write the SLA policy down and get it approved. Start with:

   | Severity | Fix within | Notes |
   |---|---|---|
   | Critical | 7 days | 72 hours if on CISA KEV and internet-facing |
   | High | 30 days | |
   | Medium | 90 days | |
   | Low | 180 days or next major release | |
   | Info | No SLA | Track only |

   The clock starts at first seen, not at triage, and does not reset on reimport. Severity here is the adjusted priority from step 4, not raw scanner severity.
3. Dedupe before counting. Build a key per finding type and merge on it (details in [references/dedupe-and-scoring.md](references/dedupe-and-scoring.md)):
   - Dependencies: `CVE or GHSA ID + package name + fixed version + asset`. The same CVE from Trivy, Snyk and Dependabot on one repo is one finding with three sources.
   - Code: `CWE + repo + file + line (or enclosing function)`. Semgrep and CodeQL hitting the same SQL injection is one finding.
   - Containers: `CVE + package + base image digest`. Fixing the base image closes it for every service that uses it, so track it once against the image owner.
   - Keep the earliest first-seen date and the highest severity across sources.
4. Prioritize. Start from CVSS base, then adjust:
   - CISA KEV listed: raise to Critical. Known exploitation beats any score.
   - EPSS at or above 0.1 (10 percent chance of exploitation in 30 days): raise one level. Below 0.01 with no KEV entry: candidate to lower one level.
   - Reachability: SCA or call graph shows the vulnerable function is never called, lower one level and record the evidence. Unknown counts as reachable.
   - Exposure: internet-facing raises one level, internal only stays, offline build tool or test dependency lowers one level.
   - Data: assets holding regulated or customer data do not get lowered below High for a Critical CVSS.
   Write the inputs next to the result so anyone can recompute it.
5. Assign an owner per finding. Map asset to team with a file the program owns (`CODEOWNERS`, a service catalog, or DefectDojo product owner). Base image findings go to the platform team. A finding with no owner is a bug in the mapping; fix the mapping, then the finding.
6. Handle exceptions. Accepting risk or delaying a fix needs a record with: finding ID, reason, compensating control, approver (not the requester), and an expiry date no longer than 90 days for High and above. In DefectDojo use Risk Acceptance with an expiration date; in Jira or GitHub use a `risk-accepted` label plus an `accepted-until` field. Expired exceptions count as breached.
7. Run the cadence:
   - Every scan: reimport, dedupe, auto-close findings that no longer appear, open tickets for new ones.
   - Weekly: list findings due in 7 days and breached findings per owner. Send each team its own list.
   - Monthly: the report in Output format. Run `python3 scripts/sla_report.py findings.csv` on an export for status, aging buckets and MTTR.
8. Close the loop. A finding is closed when a rescan no longer reports it, not when a ticket is moved to Done. Measure MTTR from first seen to verified close.

## Checklist

Program setup:

- [ ] One system of record, every scanner imports into it on a schedule.
- [ ] SLA policy written, approved and linked from the tracker.
- [ ] Dedupe keys defined for dependencies, code and containers.
- [ ] Asset to owner mapping covers every repo and image.
- [ ] Exception template with approver and expiry; expiry is enforced.
- [ ] Scanner severities mapped to the program's five levels.

Per finding:

- [ ] Has an owner, a first-seen date and a due date.
- [ ] Priority shows CVSS, EPSS, KEV, reachability and exposure inputs.
- [ ] Duplicates from other scanners linked, not counted twice.
- [ ] Closed only after a rescan confirms the fix.

Report:

- [ ] Counts are deduped findings, not raw scanner rows.
- [ ] Breached list names owners and days overdue.
- [ ] Exceptions expiring in the next 30 days listed.
- [ ] MTTR per severity, and the share closed within SLA.
- [ ] Trend against last period, not only a snapshot.

Common mistakes:

- Sorting by CVSS alone and spending a sprint on a 9.8 in a test-only dependency while a KEV-listed 7.5 on the login service waits.
- Resetting first-seen when a scanner is swapped or a repo is renamed, which hides old debt.
- Counting the same CVE in 40 microservices as 40 tasks when one base image bump fixes all of them.
- Exceptions with no expiry, which turn into permanent accepted risk nobody reviews.
- Treating "ticket closed" as "vulnerability fixed".

## Output format

Monthly report, in this order:

### Summary

Two or three sentences: open deduped findings by severity, change since last month, number of SLA breaches, the single biggest risk.

### SLA status (open findings)

| Severity | Open | Within SLA | Due in 7 days | Breached | Excepted |
|---|---|---|---|---|---|

### Aging (days since first seen)

| Severity | 0-30 | 31-60 | 61-90 | 91-180 | 180+ |
|---|---|---|---|---|---|

### Breached findings

| ID | Finding | Asset | Priority (inputs) | Owner | Days overdue | Next step |
|---|---|---|---|---|---|---|

### Exceptions

| ID | Finding | Reason | Compensating control | Approver | Expires |
|---|---|---|---|---|---|

### MTTR

| Severity | Closed this period | Mean days | Median days | Closed within SLA |
|---|---|---|---|---|

For a single prioritization question, reply with the ranked table only: ID, finding, CVSS, EPSS, KEV, reachable, exposure, final priority, due date.

## Examples

### Bad

> We have 1,214 vulnerabilities: 87 critical, 402 high. Please fix all criticals this week.

Raw scanner rows, counted three times where Trivy, Snyk and Dependabot overlap. No owners, no dates, and "critical" is the scanner's CVSS, so a test-only dependency sits next to an exploited bug.

### Good

> 312 open findings after dedupe (from 1,214 scanner rows). 4 Critical, 3 of them breached.

| ID | Finding | CVSS | EPSS | KEV | Reachable | Exposure | Priority | Owner | Due |
|---|---|---|---|---|---|---|---|---|---|
| VM-101 | CVE-2023-44487 in `golang.org/x/net` (Trivy, Dependabot) | 7.5 | 0.94 | Yes | Yes | Internet | Critical | team-api | 2026-11-10 |
| VM-117 | CWE-89 `orders/views.py:42` (Semgrep, CodeQL) | 9.8 | n/a | n/a | Yes | Internet | Critical | team-orders | 2026-11-12 |
| VM-140 | CVE-2024-12345 in `lodash` dev dependency (Snyk) | 9.1 | 0.002 | No | No (build only) | None | Medium | team-web | 2027-02-01 |

VM-101 jumps ahead of a higher CVSS because it is on KEV and the service is public. VM-140 drops to Medium with the reachability evidence attached, and comes back to Critical if the package moves into runtime dependencies.
