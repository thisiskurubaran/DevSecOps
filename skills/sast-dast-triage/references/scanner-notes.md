# Scanner notes

Commands, useful output fields, and rules that tend to be noisy. Check the tool's docs for your version, flags change.

## Semgrep

- Run: `semgrep --config auto --sarif -o semgrep.sarif .` or `semgrep --config p/owasp-top-ten --json -o semgrep.json .`
- New findings only: `semgrep ci --baseline-commit origin/main`
- Fields: `check_id`, `path`, `start.line`, `extra.severity`, `extra.metadata.cwe`, `extra.metadata.confidence`.
- Noisy: generic `audit` rules (they flag patterns, not taint). Prefer taint-mode rules for SQLi and XSS. Rules with `confidence: LOW` need extra reading.
- Tuning: write a project rule with `pattern-not` or `pattern-sanitizer` for your own safe wrapper.

## CodeQL

- Run locally: `codeql database create db --language=python` then `codeql database analyze db codeql/python-queries:codeql-suites/python-security-extended.qls --format=sarif-latest --output=codeql.sarif`
- Alerts via API: `gh api repos/{owner}/{repo}/code-scanning/alerts --paginate -q '.[] | {number, rule: .rule.id, sev: .rule.security_severity_level, path: .most_recent_instance.location.path, line: .most_recent_instance.location.start_line}'`
- Dismiss: `gh api -X PATCH repos/{owner}/{repo}/code-scanning/alerts/{n} -f state=dismissed -f dismissed_reason="false positive" -f dismissed_comment="..."`
- Path queries show source to sink. Read the whole path before deciding.
- Tuning: model custom sanitizers with data extension packs (`.yml` models) instead of dismissing each alert.

## SonarQube / SonarCloud

- Separate "Vulnerabilities" (confirmed by rule) from "Security Hotspots" (need human review). Hotspots are not findings until reviewed.
- Export: `GET /api/issues/search?componentKeys=<key>&types=VULNERABILITY&ps=500`
- Use the "new code" quality gate so legacy issues do not block PRs.

## Bandit (Python)

- Run: `bandit -r src -f json -o bandit.json -ll -ii` (medium severity and confidence and up).
- Noisy: B101 (`assert`), B311 (`random` for non-crypto use), B105/B106 (hardcoded password strings that are field names).
- Exclude tests: `bandit -r src -x tests`.

## gosec (Go)

- Run: `gosec -fmt sarif -out gosec.sarif ./...`
- Noisy: G104 (unchecked errors, better caught by `errcheck`), G304 (file path from variable) when the path is built from config.

## Snyk Code

- Run: `snyk code test --sarif-file-output=snyk.sarif`
- Ignore with reason: `snyk ignore --id=<issue-id> --reason="..." --expiry=YYYY-MM-DD`.

## OWASP ZAP

- Baseline (passive): `docker run -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t https://staging.example.com -J zap.json`
- Full (active, only against environments you own): `zap-full-scan.py`.
- API: `zap-api-scan.py -t openapi.json -f openapi`.
- Generate a config to tune rules: `zap-baseline.py -t ... -g zap.conf`, then set rules to `IGNORE`, `WARN` or `FAIL`.
- Noisy: "Cookie without SameSite" on third-party cookies, "Information disclosure: suspicious comments" on minified JS, CSP findings on API-only hosts.

## Burp Suite

- Confidence "Certain" plus a request and response pair is a strong signal. "Tentative" needs manual repeat in Repeater.

## Nuclei

- Run: `nuclei -u https://staging.example.com -severity medium,high,critical -jsonl -o nuclei.jsonl`
- Template matches on version strings can be wrong when banners are stale or backported. Confirm the version and patch level.

## SARIF quick facts

- Results live in `runs[].results[]`. Rule metadata in `runs[].tool.driver.rules[]`.
- Location: `results[].locations[0].physicalLocation.artifactLocation.uri` and `.region.startLine`.
- Severity: `results[].level` (`error`, `warning`, `note`) or `rules[].properties["security-severity"]` (CVSS-like number).
- Dedup by `partialFingerprints` when present.
