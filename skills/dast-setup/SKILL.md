---
name: dast-setup
description: Set up dynamic application security testing in CI against preview or staging environments with OWASP ZAP (baseline, full and API scan actions, Automation Framework plans, authenticated scans, rules.tsv) and Nuclei (templates, tags, severity filters, rate limits), including scope and safety limits, baselining so only new high findings fail the build, SARIF or report upload, and PR vs nightly scheduling. Use when the user asks to add ZAP or Nuclei to a pipeline, scan a running web app or API in CI, write a ZAP plan or rules.tsv, or set up authenticated or scheduled DAST.
---

# DAST Setup

Scan the running app the way an attacker would, from the outside, in an environment you own. Static tools read code; DAST finds what only shows up at runtime: missing headers, cookie flags, reflected input, exposed admin paths, verbose errors. The hard parts are scope, auth and noise, not the scanner command.

## When to use

- The user wants ZAP or Nuclei added to GitHub Actions (or another CI) against a preview, review app or staging URL.
- The user asks for a ZAP Automation Framework plan, a `rules.tsv`, or help getting an authenticated ZAP scan to stay logged in.
- The user wants an OpenAPI or GraphQL API scanned in CI.
- A DAST job is too slow, too noisy, or fails on every run and needs a baseline.
- Someone asks how to split quick PR scans from a nightly full scan.

Not for: deciding which findings are real (use `sast-dast-triage`), reviewing an API spec for design flaws (use `api-security-review`), general pipeline structure, tokens and gates (use `cicd-pipeline-builder`), or fixing header findings such as CSP and HSTS in app or proxy config (use `security-headers`).

## Steps

1. Confirm scope and ownership. Get the exact target URLs and confirm the team owns them. Write them down as the allowed scope. Never point a scan at production or a third-party host without written approval from the owner. Active scans send attack payloads and can create, change or delete data.
2. Pick the target environment. Prefer a per-PR preview or a dedicated staging stack with seed data. Use test accounts made for scanning, never a real user. Reset or reseed the data after full scans.
3. Pick the scan type:
   - PR: ZAP baseline (`zaproxy/action-baseline`). Spider plus passive rules only, no attacks, a few minutes.
   - API: ZAP API scan (`zaproxy/action-api-scan`) with `format: openapi`, `soap` or `graphql` and the spec URL or file as `target`.
   - Nightly: ZAP full scan (`zaproxy/action-full-scan`) or an Automation Framework plan with `activeScan`, against staging only.
   - Known issues and exposures: Nuclei with a filtered template set, PR or nightly.
4. Exclude what must not be hit: logout, delete and admin endpoints, password reset, payment, email or SMS senders, and any third-party domain. In ZAP use context `excludePaths` (regex). In Nuclei, use `-etags dos,intrusive,fuzz` and pass only in-scope URLs.
5. Set rate limits. ZAP: `threadPerHost` and `maxScanDurationInMins` on `activeScan`. Nuclei: `-rl` (requests per second) and `-c` (concurrent templates). Start low on shared staging and tell whoever runs it.
6. Set up auth when the app is mostly behind login. Use an Automation Framework context with `authentication`, `sessionManagement`, `users` and a `verification` regex so ZAP knows when it was logged out. Pass credentials from CI secrets through env vars (`${ZAP_USER}`), never in the plan file. See [references/zap-automation-plan.md](references/zap-automation-plan.md).
7. Tune with `rules.tsv` for the packaged scans. One line per alert ID: `IGNORE`, `WARN` or `FAIL`. Set the alerts you care about to `FAIL`, pass `-I` in `cmd_options` so plain warnings do not fail the job, and give every `IGNORE` a reason in the third column.
8. Baseline. Run once on the current app, triage, and store the accepted findings (ZAP plugin ID plus URL, Nuclei template ID plus matched URL). Fail the job only on new High findings that are not in the baseline. Review the baseline when it grows.
9. Publish results. Upload HTML and JSON reports as artifacts. Upload SARIF to code scanning with `github/codeql-action/upload-sarif` (needs `security-events: write`) so findings show on the PR. Nuclei writes SARIF with `-sarif-export`; ZAP plans write it with the `sarif-json` report template.
10. Hand off. Send new findings to `sast-dast-triage` with the report, the target URL, the scan type and the commit SHA. Header findings go to `security-headers`.

## Checklist

Scope and safety:

- Target URLs are written down and owned by the team. No production target without recorded approval.
- Active scans run only against staging or a throwaway preview, never shared demo data.
- Logout, delete, reset, payment and messaging endpoints are excluded.
- Third-party hosts (CDNs, auth providers, analytics) are out of scope.
- Rate limits and a max duration are set on every scan.
- Scans run as dedicated test accounts with the least role that still reaches the features under test.

Pipeline:

- Every `uses:` is pinned to a full commit SHA with a version comment.
- Top-level `permissions: contents: read`; the job gets `security-events: write` only if it uploads SARIF, and `issues: write` only if the ZAP action may open issues.
- ZAP actions have `allow_issue_writing: false` unless the team wants an issue per run.
- No DAST job with secrets runs on `pull_request` from forks. Gate on same-repo PRs or use the nightly run.
- `timeout-minutes:` set on every scan job.
- Docker images pinned to a version tag or digest (`ghcr.io/zaproxy/zaproxy:stable` is a moving tag).

Signal:

- `rules.tsv` or `alertFilter` entries are committed and each IGNORE has a reason.
- Only new High (and agreed Medium) findings fail the build. Everything else is reported.
- Reports are kept as artifacts for at least the triage window.
- The nightly job alerts someone on failure; it does not fail silently.

## Output format

When setting up DAST, deliver:

1. Workflow file(s) with a path header, ready to commit.
2. Config files: `rules.tsv`, ZAP plan YAML, Nuclei flags, baseline file.
3. A scan table:

| Scan | Trigger | Target | Tool and mode | Fails on | Results |
|---|---|---|---|---|---|
| PR baseline | pull_request (same repo) | preview URL | ZAP baseline, passive | `FAIL` rules in rules.tsv | artifact, job summary |
| Nightly full | schedule 02:17 UTC | staging.example.com | ZAP plan with activeScan | new High vs baseline | SARIF, artifact |
| Nightly Nuclei | schedule | staging.example.com | `-severity high,critical -etags dos,intrusive,fuzz -rl 20` | new High or Critical | SARIF |

4. A list of things the user must set up by hand: test accounts, CI secrets, seed data, approval for scope, who gets the nightly alert.

When reviewing an existing DAST setup, use a findings table:

| Severity | File | Line | Issue | Fix |
|---|---|---|---|---|
| High | .github/workflows/dast.yml | 18 | Full active scan targets the production URL on every PR | Point at the preview URL, move active scan to nightly staging |

Severity: Critical (active scan against production or a third party, real credentials in the repo), High (no exclusions for destructive endpoints, secrets exposed to fork PRs), Medium (no rate limit, no baseline so the job is ignored, unpinned actions), Low (missing artifacts, timeouts, reasons on IGNORE lines).

## Examples

Bad: full active scan against production on every PR, tag-pinned action, no rules or limits.

```yaml
on: [pull_request]
jobs:
  zap:
    runs-on: ubuntu-latest
    steps:
      - uses: zaproxy/action-full-scan@v0
        with:
          target: https://www.example.com
```

Good: passive baseline on same-repo PRs against the preview, active scan nightly on staging, pinned, tuned.

```yaml
# .github/workflows/dast-pr.yml
on: pull_request
permissions:
  contents: read
jobs:
  zap-baseline:
    if: github.event.pull_request.head.repo.full_name == github.repository
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@<full-commit-sha> # v7.0.1
        with:
          persist-credentials: false
      - uses: zaproxy/action-baseline@<full-commit-sha> # v0.15.0
        with:
          target: https://pr-${{ github.event.pull_request.number }}.preview.example.com
          rules_file_name: .zap/rules.tsv
          cmd_options: -I
          allow_issue_writing: false
```

```tsv
10035	WARN	(Strict-Transport-Security Header Not Set: handled by security-headers work, ticket SEC-101)
10038	FAIL	(Content Security Policy Header Not Set)
10096	IGNORE	(Timestamp Disclosure: build IDs in static assets, not sensitive)
90022	FAIL	(Application Error Disclosure)
```

Columns in `rules.tsv` are separated by a real tab, not spaces.

```yaml
# .github/workflows/dast-nightly.yml (Nuclei job)
on:
  schedule:
    - cron: "17 2 * * *"
  workflow_dispatch:
permissions:
  contents: read
jobs:
  nuclei:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    permissions:
      contents: read
      security-events: write
    steps:
      - name: Nuclei
        run: |
          docker run --rm -v "$PWD:/out" projectdiscovery/nuclei:v3.11.1 \
            -u https://staging.example.com \
            -severity high,critical -etags dos,intrusive,fuzz \
            -rl 20 -c 10 -jsonl -o /out/nuclei.jsonl -sarif-export /out/nuclei.sarif
      - uses: github/codeql-action/upload-sarif@<full-commit-sha> # v4.39.3
        with:
          sarif_file: nuclei.sarif
          category: nuclei
```

Replace each `<full-commit-sha>` with the 40-character SHA for that release tag on the upstream repo before committing. The nightly ZAP plan job, auth config and the new-findings check are in [references/zap-automation-plan.md](references/zap-automation-plan.md).
