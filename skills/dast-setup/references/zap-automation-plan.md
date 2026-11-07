# ZAP Automation Framework plan for authenticated nightly scans

A plan file drives ZAP without the packaged scan scripts. Use it when you need login, custom exclusions, an active scan with limits, or SARIF output.

## Plan

```yaml
# .zap/nightly.yaml
env:
  contexts:
    - name: staging
      urls:
        - https://staging.example.com
      includePaths:
        - "https://staging\\.example\\.com.*"
      excludePaths:
        - ".*/logout.*"
        - ".*/account/delete.*"
        - ".*/password/reset.*"
        - ".*/admin/.*"
        - ".*/checkout/pay.*"
      authentication:
        method: form
        parameters:
          loginPageUrl: https://staging.example.com/login
          loginRequestUrl: https://staging.example.com/login
          loginRequestBody: "username={%username%}&password={%password%}"
        verification:
          method: response
          loggedInRegex: "\\QSign out\\E"
          loggedOutRegex: "\\QSign in\\E"
      sessionManagement:
        method: cookie
      users:
        - name: dast-user
          credentials:
            username: ${ZAP_USER}
            password: ${ZAP_PASS}
  parameters:
    failOnError: true
    progressToStdout: true

jobs:
  - type: spider
    parameters:
      context: staging
      user: dast-user
      maxDuration: 10
  - type: passiveScan-wait
    parameters:
      maxDuration: 10
  - type: activeScan
    parameters:
      context: staging
      user: dast-user
      threadPerHost: 2
      maxRuleDurationInMins: 5
      maxScanDurationInMins: 60
  - type: alertFilter
    alertFilters:
      - ruleId: 10096
        newRisk: "False Positive"
  - type: report
    parameters:
      template: traditional-json
      reportDir: /zap/wrk
      reportFile: zap-nightly
  - type: report
    parameters:
      template: sarif-json
      reportDir: /zap/wrk
      reportFile: zap-nightly-sarif
```

Notes:

- `excludePaths` and `includePaths` are regexes matched against the full URL. Escape dots in hostnames.
- `loggedInRegex` and `loggedOutRegex` let ZAP notice a dropped session and log in again. Pick text that only appears in one state.
- For a JSON login API, set `authentication.method: json` and send a JSON body in `loginRequestBody`. For token auth in a header, `sessionManagement.method: headers` is an option, but test it on one request first.
- Keep `${ZAP_USER}` and `${ZAP_PASS}` as env var references. ZAP fills them in at run time.
- Generate a starting plan from the ZAP desktop UI (Automation tab) and trim it, rather than writing every key by hand.

## Workflow job

```yaml
# .github/workflows/dast-nightly.yml (ZAP job)
  zap-full:
    runs-on: ubuntu-latest
    timeout-minutes: 90
    environment: staging-dast
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@<full-commit-sha> # v7.0.1
        with:
          persist-credentials: false
      - name: ZAP plan
        env:
          ZAP_USER: ${{ secrets.DAST_USER }}
          ZAP_PASS: ${{ secrets.DAST_PASS }}
        run: |
          chmod a+w .zap
          docker run --rm -v "$PWD/.zap:/zap/wrk:rw" \
            -e ZAP_USER -e ZAP_PASS \
            ghcr.io/zaproxy/zaproxy:2.17.0 \
            zap.sh -cmd -autorun /zap/wrk/nightly.yaml
      - uses: actions/upload-artifact@<full-commit-sha> # v7.0.2
        if: always()
        with:
          name: zap-nightly
          path: .zap/zap-nightly*
      - uses: github/codeql-action/upload-sarif@<full-commit-sha> # v4.39.3
        if: always()
        with:
          sarif_file: .zap/zap-nightly-sarif.json
          category: zap
      - name: Fail on new High
        run: ./.zap/new-highs.sh .zap/zap-nightly.json .zap/baseline.txt
```

Use a different `reportFile` per template so the JSON and SARIF reports do not overwrite each other. Check the file names ZAP writes in your version after the first run and adjust the upload paths.

## New findings only

Store accepted findings as `pluginid uri` lines in `.zap/baseline.txt`, sorted. The check pulls High alerts (`riskcode` "3") from the traditional JSON report and fails if any line is not in the baseline.

```bash
#!/usr/bin/env bash
# .zap/new-highs.sh <report.json> <baseline.txt>
set -euo pipefail
report="$1"
baseline="$2"
jq -r '.site[].alerts[] | select(.riskcode == "3")
       | .pluginid as $id | .instances[] | "\($id) \(.uri)"' "$report" \
  | sort -u > current-highs.txt
new=$(comm -23 current-highs.txt <(sort -u "$baseline"))
if [ -n "$new" ]; then
  echo "New High findings:"
  echo "$new"
  exit 1
fi
echo "No new High findings."
```

Same idea for Nuclei with the JSONL output:

```bash
jq -r '"\(."template-id") \(."matched-at")"' nuclei.jsonl | sort -u > current.txt
comm -23 current.txt <(sort -u .nuclei/baseline.txt)
```

URLs with IDs or tokens in them change between runs. Normalize them (strip query strings, replace numeric path segments) before comparing, or the baseline never matches.
