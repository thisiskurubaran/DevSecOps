---
name: risk-acceptance
description: Write and review security exception and risk acceptance records for findings that cannot be fixed within SLA, with finding reference, affected assets, likelihood and impact rationale, concrete compensating controls, owner and approver roles, a hard expiry, review triggers and closure criteria, plus matching scanner suppressions (.trivyignore exp, nosemgrep, Checkov skip, VEX). Use when the user asks to accept a risk, request or approve a security exception, delay a fix past SLA, suppress a scanner finding for business reasons, or review exceptions that are expiring.
---

# Risk Acceptance

A risk acceptance says: we know about this finding, we are not fixing it yet, here is why, here is what limits the damage, and here is the date it stops being acceptable. Without that last part it is just a finding someone stopped looking at.

## When to use

- A finding will miss its remediation SLA and the owner wants a formal exception.
- Someone asks to "accept the risk", "waive" or "defer" a CVE, scanner rule or pentest finding.
- A reviewer or approver needs to decide whether an exception request is good enough to sign.
- A scanner suppression (`.trivyignore`, `nosemgrep`, Checkov skip, VEX statement) needs a record behind it.
- Exceptions are expiring this month and need renewal, closure or escalation.

Not for: setting SLAs, tracking the backlog or reporting aging (use `vuln-management`), deciding whether a finding is a true or false positive (use `sast-dast-triage`; a false positive gets closed, not accepted), writing OPA or Kyverno rules that enforce exception expiry in CI (use `policy-as-code`), or finding risks in a new design (use `threat-modeling`).

## Steps

1. Confirm the finding is real and in scope. If it is a false positive, stop and close it as one. If it is not exploitable in this asset (vulnerable code not shipped or not reachable), that is a VEX `not_affected` statement with evidence, not an acceptance. Acceptance is for findings that are real and affect the asset.
2. Pin the finding reference. Use the identifier the scanner or tester produced: `CVE-2024-12345` in `libexample 1.4.2`, Semgrep rule `python.lang.security.audit.dangerous-subprocess-use`, Checkov `CKV_AWS_20`, pentest `PT-2026-031`. Link the tracker ticket (`VM-140`, DefectDojo finding ID).
3. List affected assets exactly: repo, service, image digest, cloud account and resource ID, environment. "Prod" is not an asset.
4. Describe the risk in plain language. One or two sentences a product manager can read: who could do what to which data. No CVSS vector in this field.
5. Rate likelihood and impact (Low, Medium, High) with a rationale for each. Likelihood cites exposure, EPSS, CISA KEV status, required privileges and reachability. Impact cites the data and systems an attacker reaches. The rating without a reason is rejected.
6. State why it cannot be fixed now. Acceptable reasons are specific: no upstream fix released, fix requires a major version upgrade scheduled for a named sprint, vendor appliance with no patch, fix breaks a contractual integration until a dated migration. "Not a priority" or "too much work" is not a reason.
7. List compensating controls that can be checked. Each control names the thing and where to verify it:
   - WAF rule `waf-rule-1042` blocking the vulnerable path, in block mode, not count mode.
   - Kubernetes NetworkPolicy `deny-ingress-legacy-pdf` limiting ingress to the gateway namespace.
   - Feature flag `pdf_import_v1` off in production, change requires security approval.
   - Alert `legacy-pdf-5xx-spike` routed to the on-call security channel.
   Controls that cannot be pointed at ("we monitor it", "behind the firewall", "low traffic") do not count.
8. Set owner, approver and dates. The business owner is a role that owns the asset (for example "Payments engineering lead"). The security approver is a different role ("AppSec lead", "CISO for Critical"). Never the same person, never real names in the public template. Expiry limits from approval date:

   | Severity | Max expiry | Approver |
   |---|---|---|
   | Critical | 30 days | CISO or delegate |
   | High | 90 days | Security lead |
   | Medium | 180 days | AppSec engineer |
   | Low | 365 days | Team lead with AppSec notified |

   Adjust to the org's policy, but every record has an expiry. Renewal is a new approval with fresh evidence, not a date edit.
9. Write review triggers that reopen the record before expiry: finding added to CISA KEV, public exploit or EPSS jump above 0.1, asset becomes internet-facing or starts holding new data classes, compensating control removed or changed, upstream fix released.
10. Write closure criteria: the fix that ends the exception and how it is verified (rescan no longer reports the finding, pentest retest passes). Closing also removes the scanner suppression.
11. Store it and link the suppression. See [references/record-template.md](references/record-template.md) for the full template and suppression syntax.
    - Repo: `security/exceptions/EXC-0012.md`, changed through PRs with CODEOWNERS requiring the security team.
    - GRC tool or DefectDojo Risk Acceptance with expiration date set.
    - Jira: issue type or label `risk-accepted` with `accepted-until` field.
    Every suppression in code carries the exception ID and an expiry so the scanner fails again when it lapses:
    ```
    # .trivyignore
    # EXC-0012 expires 2027-01-31, see security/exceptions/EXC-0012.md
    CVE-2024-12345 exp:2027-01-31
    ```
12. Review expiring records on a schedule. Monthly, list everything expiring in the next 30 days. For each: closed (fix shipped and verified), renewed (new approval, controls re-verified, reason still valid), or escalated (owner missed it, finding counts as SLA breach). An expired record with no decision is a breach, not a silent extension.

## Checklist

Reject the request if any of these fail:

- [ ] Finding reference is a specific ID with package, version or rule, not "some CVEs".
- [ ] Assets listed by repo, image digest or resource ID.
- [ ] Risk description is plain language and says what an attacker gets.
- [ ] Likelihood and impact each have a rationale.
- [ ] Reason it cannot be fixed is specific and has a date or dependency.
- [ ] Every compensating control names a rule, policy, flag or alert that can be checked.
- [ ] Owner and approver are different roles.
- [ ] Expiry is set and within the limit for the severity. No "permanent", "indefinite" or "until further notice".
- [ ] Review triggers include KEV listing, new exploit and scope change.
- [ ] Closure criteria say what fix and what verification.
- [ ] Linked scanner suppression references the exception ID and expires on the same date.

Common weak requests:

- "Accepted forever" or a blank expiry. Send back with the maximum allowed date.
- Controls like "monitoring in place" or "internal only". Ask which alert, which network rule.
- The requester approving their own exception.
- One record covering "all medium findings in repo X". One finding per record, or one CVE across a listed set of assets.
- A blanket `.trivyignore` or `#nosec` with no ID and no date, added before any record exists.
- Renewing three times in a row with the same reason. Escalate to the next approval level.

## Output format

For a new record, fill this template (full version with field notes in [references/record-template.md](references/record-template.md)):

```markdown
# EXC-0000: <short title>

| Field | Value |
|---|---|
| Status | Proposed / Approved / Expired / Closed |
| Finding | <CVE, rule ID or pentest ID>, tracker <link> |
| Severity | <program severity> |
| Assets | <repo, image digest, resource ID, env> |
| Business owner | <role> |
| Security approver | <role> |
| Approved | YYYY-MM-DD |
| Expires | YYYY-MM-DD |

## Risk
## Likelihood and impact
## Why it cannot be fixed now
## Compensating controls
## Review triggers
## Closure criteria
## Linked suppressions
```

For a review of a request, reply with a verdict (Approve, Approve with changes, Reject) and a table: field, problem, required change.

For an expiry review, reply with a table: ID, finding, owner role, expires, decision (close, renew, escalate), reason.

## Examples

### Bad

> **EXC: Accept log4j risk**
> Finding: log4j vulnerabilities in our Java services.
> Reason: Upgrading is a lot of work and the services are internal.
> Controls: Behind the firewall, we monitor logs.
> Approved by: the team. Expiry: none.

No CVE, no version, no asset list. "Internal" and "monitor logs" cannot be checked. The team approved its own risk, and there is no expiry, so it will never be looked at again. Reject.

### Good

> **EXC-0012: CVE-2024-12345 in libexample on pdf-import service**
> Finding: CVE-2024-12345 in `libexample 1.4.2`, Trivy, tracker VM-140. Severity High.
> Assets: `pdf-import` service, image `registry.example.com/pdf-import@sha256:3f1a...`, prod and staging.
> Risk: A crafted PDF upload could run code in the pdf-import pod, which can read the uploads bucket.
> Likelihood: Medium. Upload endpoint is authenticated, EPSS 0.03, not on KEV. Impact: High. Uploads bucket holds customer documents.
> Why not now: fix is only in `libexample 2.x`, which drops the API we use. Migration ticket VM-151 is planned for the January sprint.
> Controls: WAF rule `waf-rule-1042` blocks PDFs over 5 MB and embedded JavaScript on `/upload`, block mode. NetworkPolicy `deny-egress-pdf-import` allows egress only to the uploads bucket endpoint. Alert `pdf-import-crash-loop` pages security on-call.
> Owner: Documents team engineering lead. Approver: Security lead. Approved 2026-11-02, expires 2027-01-31.
> Review triggers: KEV listing, public exploit, EPSS above 0.1, endpoint opened to unauthenticated users, WAF rule set to count mode.
> Closure: `pdf-import` on `libexample 2.x` and Trivy rescan no longer reports CVE-2024-12345. Remove the `.trivyignore` entry in the same PR.
> Suppression: `.trivyignore` line `CVE-2024-12345 exp:2027-01-31` with a comment pointing to EXC-0012.
