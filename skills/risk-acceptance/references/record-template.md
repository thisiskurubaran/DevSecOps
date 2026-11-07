# Risk acceptance record template

Copy this file to `security/exceptions/EXC-NNNN.md` (or paste the fields into your GRC tool or Jira issue). One finding per record. If the same CVE affects several assets, list them all in one record only when the reason, controls and expiry are the same for each.

```markdown
# EXC-NNNN: <finding ID> in <component> on <asset>

| Field | Value |
|---|---|
| Status | Proposed |
| Finding | <CVE-YYYY-NNNNN in package x.y.z / scanner rule ID / pentest ID> |
| Source | <Trivy, Snyk, Semgrep, Checkov, pentest report name> |
| Tracker | <VM-123 or DefectDojo finding ID> |
| Severity | <Critical / High / Medium / Low, program severity not raw CVSS> |
| Assets | <repo, service, image digest, cloud resource ID, environments> |
| Business owner | <role that owns the asset, e.g. Payments engineering lead> |
| Security approver | <role, different from owner, e.g. Security lead> |
| Requested | YYYY-MM-DD |
| Approved | YYYY-MM-DD |
| Expires | YYYY-MM-DD (Critical 30d, High 90d, Medium 180d, Low 365d max) |
| Renewal count | 0 |

## Risk

One or two plain sentences: who could do what, to which data or system.

## Likelihood and impact

- Likelihood: <Low / Medium / High>. Exposure (internet, internal, offline), auth required,
  EPSS score and date, CISA KEV yes or no, reachability evidence.
- Impact: <Low / Medium / High>. Data classes and systems reachable, blast radius.

## Why it cannot be fixed now

Specific blocker and the date or dependency that removes it. Link the fix ticket.

## Compensating controls

| Control | Type | Where to verify | Verified on |
|---|---|---|---|
| waf-rule-NNNN, block mode | WAF | WAF console, rule set <name> | YYYY-MM-DD |
| NetworkPolicy <name> | Network | `kubectl get netpol <name> -n <ns>` | YYYY-MM-DD |
| Feature flag <name> off in prod | Feature flag | Flag service, prod env | YYYY-MM-DD |
| Alert <name> to security on-call | Detection | Alerting config repo path | YYYY-MM-DD |

## Review triggers

Reopen this record before expiry if any of these happen:

- Finding added to CISA KEV.
- Public exploit released or EPSS rises above 0.1.
- Asset becomes internet-facing, loses auth, or starts storing a new data class.
- Any compensating control above is removed, disabled or changed to monitor mode.
- Upstream fix becomes available.

## Closure criteria

- Fix: <upgrade, config change, code change>.
- Verification: <rescan with scanner X no longer reports it / pentest retest ID>.
- Suppressions listed below removed in the same change.

## Linked suppressions

- <file path and line>

## History

| Date | Event | By (role) |
|---|---|---|
| YYYY-MM-DD | Requested | <role> |
| YYYY-MM-DD | Approved | <role> |
```

## Scanner suppression syntax

Every suppression names the exception ID and, where the tool supports it, an expiry that makes the scanner fail again on the same date as the record.

Trivy, `.trivyignore`:

```
# EXC-0012 expires 2027-01-31, security/exceptions/EXC-0012.md
CVE-2024-12345 exp:2027-01-31
```

Trivy, `.trivyignore.yaml`:

```yaml
vulnerabilities:
  - id: CVE-2024-12345
    paths: ["app/requirements.txt"]
    statement: "EXC-0012, accepted until 2027-01-31"
    expired_at: 2027-01-31
```

Semgrep, inline (no built-in expiry, so the comment above must carry the ID and date):

```python
# EXC-0019 until 2027-03-31: cmd is built from a fixed allowlist
subprocess.run(cmd, shell=True)  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use
```

Checkov, inline in Terraform:

```hcl
resource "aws_s3_bucket" "legacy_exports" {
  #checkov:skip=CKV_AWS_18:EXC-0021 until 2027-02-28, access logging blocked by vendor bucket policy
  bucket = "legacy-exports-example"
}
```

VEX (OpenVEX) for findings that do not affect the product. This is not a risk acceptance and needs evidence, not an expiry:

```json
{
  "vulnerability": { "name": "CVE-2024-23456" },
  "products": [{ "@id": "pkg:oci/pdf-import@sha256:3f1a" }],
  "status": "not_affected",
  "justification": "vulnerable_code_not_in_execute_path",
  "impact_statement": "The XML parser module is never loaded; see VM-162 call graph."
}
```

If the vulnerable code is present and reachable, the status is `affected` and the risk acceptance record covers it. Do not use `not_affected` to hide an accepted risk.

## Finding suppressions without a record

Run this in CI or during the monthly review to list suppressions that lack an exception ID:

```bash
grep -rnE -B1 'nosemgrep|checkov:skip|#nosec' --include='*.py' --include='*.tf' --include='*.go' --include='*.js' . | grep -vE 'EXC-[0-9]{4}'
# review the output by hand: a hit is fine if the line above carries the EXC ID
grep -vE '^\s*(#|$)' .trivyignore | grep -v 'exp:'
```
