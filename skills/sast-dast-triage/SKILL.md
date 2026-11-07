---
name: sast-dast-triage
description: Triage SAST and DAST scanner output (Semgrep, CodeQL, SonarQube, Bandit, gosec, Snyk Code, OWASP ZAP, Burp, Nuclei) into true positives and false positives, rank the real ones by exploitability and impact, and write suppressions with reasons. Use when the user shares a SARIF file, scanner JSON or report, a list of code scanning alerts, or asks which scanner findings are real and what to fix first.
---

# SAST/DAST Triage

Scanners are noisy. This skill turns a pile of alerts into a short, ranked list of real issues and a documented set of suppressions, so the team fixes what matters and the next scan is quieter.

## When to use

- The user shares scanner output: SARIF, Semgrep JSON, CodeQL alerts, SonarQube issues export, Bandit or gosec JSON, ZAP or Burp reports, Nuclei results.
- GitHub code scanning shows dozens of open alerts and someone asks "which of these are real?"
- A CI security gate is failing and the team needs to decide fix, suppress, or accept.
- The user wants baseline and suppression rules so old findings stop blocking PRs.

Not for: a manual audit with no scanner output (use `security-audit`), CVEs in third-party packages from SCA tools like Dependabot, Snyk Open Source or `npm audit` (use `dependency-supply-chain`), container image scan results from Trivy or Grype (use `container-security`), or secret scanner hits (use `secrets-management`).

## Steps

1. Get the raw output, not a screenshot. Ask for SARIF or JSON:
   - `semgrep --config auto --sarif -o semgrep.sarif .`
   - `gh api repos/{owner}/{repo}/code-scanning/alerts --paginate > alerts.json`
   - ZAP: `zap-baseline.py -t https://staging.example.com -J zap.json`
2. Summarize before reading. Group by rule, severity and file so duplicates collapse. For SARIF, run `python3 scripts/sarif_summary.py results.sarif`. For a large set, triage one rule at a time, starting with the rule that has the highest severity.
3. For each rule group, read the rule's intent (rule ID docs, CWE). Decide what a true positive must look like.
4. For each finding, open the code at the reported line with enough context (the whole function and its callers). Answer three questions:
   - Reachable: is the code path live and reachable from an entry point? Dead code, tests and build scripts are usually not.
   - Controllable: does untrusted input reach the sink without validation, encoding or parameterization that neutralizes it?
   - Impactful: if exploited, what does an attacker get?
5. Label each finding: true positive, false positive, or needs verification. A false positive needs a reason a reviewer can check ("value comes from `settings.REGION`, a constant", not "looks fine").
6. For DAST findings, reproduce with the exact request (`curl -i ...`) against a non-production target. Check the response, not only the scanner's confidence field. Map the URL back to the handler in code.
7. Rank true positives by exploitability times impact (see Output format). Scanner severity is an input, not the answer.
8. Write suppressions for false positives in the tool's native format, scoped to one line or one path, with a reason. Never disable a rule repo-wide to clear one hit.
9. Propose a baseline so CI only fails on new findings: `semgrep ci --baseline-commit origin/main`, CodeQL PR diff alerts, SonarQube "new code" quality gate.
10. Hand fixes for the top true positives to the developer with code. Note where a rule needs tuning (custom Semgrep rule, CodeQL sanitizer model) to stop repeat false positives.

## Checklist

Common false positive patterns:

- Test files, fixtures and mocks (`tests/`, `__tests__/`, `*_test.go`, `spec/`). Exclude them in scanner config instead of suppressing one by one.
- Generated code (`*.pb.go`, `dist/`, `vendor/`, `node_modules/`, migrations).
- "Hardcoded password" on a variable named `password_field` or a placeholder like `changeme` in an example config.
- SQL built with string formatting from a fixed allowlist or an enum, not user input.
- XSS on output that is JSON with `Content-Type: application/json` and no HTML rendering.
- Weak hash (MD5, SHA-1) used for cache keys or ETags, not for passwords or signatures.
- `subprocess` with `shell=False` and a constant argument list.
- DAST "missing header" findings on static asset paths or API endpoints that never render HTML.
- DAST SQLi based only on a timing difference with no confirmed payload behavior.

Signs a finding is real:

- Data flow trace (CodeQL path, Semgrep taint mode) starts at a request parameter, header, cookie or body field.
- The sanitizer the scanner missed does not exist, or is applied after the sink.
- DAST reflected payload appears unencoded in an HTML response.
- The endpoint is reachable without auth or with a low-privilege account.

Suppression formats (always include a reason):

- Semgrep: `# nosemgrep: python.lang.security.audit.formatted-sql-query -- id is int-cast on line 40`
- Bandit: `# nosec B608 -- table name from fixed enum`
- gosec: `// #nosec G204 -- args are constants`
- CodeQL: dismiss the alert in the UI or API with reason `false positive` and a comment. For repeated patterns, add a query filter in `codeql-config.yml` under `query-filters`.
- SonarQube: mark "False Positive" or "Won't Fix" with a comment, or `// NOSONAR` with a reason as last resort.
- ZAP: add a rule to the baseline config file (`-c zap.conf`) with `IGNORE` and a comment, or an alert filter scoped to a URL regex.
- Path exclusions: `.semgrepignore`, `paths-ignore` in `codeql-config.yml`, `sonar.exclusions`.

See [references/scanner-notes.md](references/scanner-notes.md) for per-tool commands, output fields and known noisy rules.

## Output format

Start with counts: total findings, true positives, false positives, needs verification. Then:

### Fix list (true positives, ranked)

| Rank | Severity | Tool / rule | File | Line | Issue | Why it is real | Fix |
|------|----------|-------------|------|------|-------|----------------|-----|

Severity after triage:

| Level | Rule |
|-------|------|
| Critical | Reachable without auth, attacker-controlled input, leads to RCE, auth bypass or bulk data access |
| High | Reachable with a normal account, real data exposure or integrity loss |
| Medium | Needs unusual conditions or user interaction, limited impact |
| Low | Defense in depth, hardening, no direct exploit path |

### False positives

| Tool / rule | File | Line | Reason | Suppression |
|-------------|------|------|--------|-------------|

### Needs verification

List each with the exact check to run.

### Config changes

Path exclusions, baseline settings, or rule tuning to cut future noise.

## Examples

### Bad triage

> Semgrep flagged 42 issues. Most look like false positives. I suppressed `formatted-sql-query` in `.semgrep.yml`.

No per-finding reasoning, and turning off the rule globally hides the next real SQL injection.

### Good triage

Finding: `python.lang.security.audit.formatted-sql-query` at `reports/export.py:88`.

```python
def export(request):
    sort = request.GET.get("sort", "created_at")
    cur.execute(f"SELECT * FROM reports ORDER BY {sort}")
```

True positive, High. `sort` comes straight from the query string. `?sort=(SELECT pg_sleep(5))` delays the response. Fix with an allowlist:

```python
ALLOWED_SORT = {"created_at", "title", "owner"}

def export(request):
    sort = request.GET.get("sort", "created_at")
    if sort not in ALLOWED_SORT:
        sort = "created_at"
    cur.execute(f"SELECT * FROM reports ORDER BY {sort}")  # nosemgrep: python.lang.security.audit.formatted-sql-query -- sort checked against ALLOWED_SORT
```

Same rule at `scripts/seed_db.py:12`: false positive. The script runs locally with constants and is not deployed. Add `scripts/` to `.semgrepignore` rather than suppressing inline.
