---
name: detection-engineering
description: Write, test and tune log detection rules as code: Sigma rules converted with sigma-cli to Splunk, Elastic or KQL, native SPL, KQL, EQL or ES|QL queries where Sigma does not fit, CI validation and sample-event tests, MITRE ATT&CK coverage mapping, cloud log sources (CloudTrail, Entra ID sign-in, Azure Activity, GCP Audit, Okta, GitHub audit log), and tuning with owned, expiring allowlists. Use when the user shares or asks for a Sigma rule or SIEM query, wants a detection for cloud or identity activity (root login, MFA disabled, new access key, CloudTrail stopped, impossible travel, mass download), asks why an alert is noisy or silent, or wants a detection-as-code pipeline.
---

# Detection Engineering

A detection is code. It needs a clear intent, a test that proves it fires, an owner, and a runbook for whoever gets paged. This skill covers writing the rule, proving it works against real log shapes, keeping its false positive rate low enough that people still read it, and handing a true positive to incident response.

## When to use

- The user shares a Sigma rule, a Splunk saved search, a KQL analytics rule, or an Elastic rule and asks for a review or fix.
- The user wants a new detection for cloud, identity or SaaS activity: root or break-glass login, MFA removed, new IAM access key, audit logging turned off, impossible travel, bulk downloads.
- An alert fires too often ("this fires 300 times a day") or never fires when it should.
- Someone wants detections in git with CI checks, tests and versioning.
- The user asks which ATT&CK techniques their rules cover and where the gaps are.

Not for: Falco or Tetragon rules for container and host runtime behavior (use `runtime-security`), handling an incident that is already confirmed (use `incident-response`), building the log, metrics or tracing pipeline itself (use `observability-setup`), or scanner findings and patch tracking (use `vuln-management`).

## Steps

1. Pin down the behavior. Write one sentence: who does what, in which log, and why it matters. "Someone stops a CloudTrail trail, which blinds us to later API calls." If you cannot write it, the rule will be vague.
2. Confirm the log source exists and has the fields you need. Ask for one raw sample event. Check retention, ingestion delay, and whether optional data is on (S3 data events in CloudTrail are off by default, so a GetObject rule on a trail without them never fires). See [references/log-sources.md](references/log-sources.md).
3. Choose the format:
   - Sigma for single-event matching on field values. It is portable and reviewable.
   - Native SPL, KQL, EQL or ES|QL when you need aggregation, joins, baselines, geo lookups or sequences that Sigma or your backend cannot express (impossible travel, mass download, "first time seen").
4. Write the Sigma rule with every required field filled in (see checklist). Generate a fresh UUID for `id` (`uuidgen` or `python -c "import uuid; print(uuid.uuid4())"`) and never reuse one. Use field names exactly as they appear in the raw event (`eventName`, `userIdentity.type`).
5. Validate and convert with sigma-cli:
   - `pip install sigma-cli`
   - `sigma check rules/` to catch schema errors, bad tags and duplicate IDs.
   - `sigma plugin list` then `sigma plugin install splunk` (or `elasticsearch`, `kusto`).
   - `sigma list targets` and `sigma list pipelines` to see what is installed.
   - `sigma convert -t splunk --without-pipeline rules/aws/` when field names already match your index. Use a processing pipeline (`-p`) when your SIEM renames fields.
   - `sigma convert -t lucene` or `-t esql` for Elastic, `-t kusto -p microsoft_xdr` for Defender XDR.
   Read the converted query. Backends handle wildcards, case and nested fields differently, and a query that converts cleanly can still match nothing.
6. Test with sample events. Keep at least one positive and one negative event per rule next to it (`tests/<rule-id>/match.json`, `tests/<rule-id>/no_match.json`). Load them into a test index or run the converted query against them in CI. A rule without a positive test is assumed broken.
7. Backtest against 30 days of production logs before enabling. Count hits, read a sample, and estimate the false positive rate. If more than a handful of hits per week are benign, tune before shipping.
8. Tune with the narrowest filter that holds. Add a `filter_*` selection in Sigma (`condition: selection and not filter_ci_role`) or an allowlist lookup in the SIEM. Every allowlist entry gets an owner, a reason and an expiry date. Prefer matching on stable identifiers (role ARN, app ID) over display names or IPs.
9. Add alert metadata: severity, ATT&CK technique, owner team, runbook URL, and the fields a responder needs on the first screen (actor, source IP, user agent, account, region, target resource).
10. Map coverage. Tag each rule with ATT&CK tactic and technique (`attack.persistence`, `attack.t1098.001`) and keep a table of techniques you care about against rules that cover them. Gaps go on the backlog, not in a slide.
11. Ship through git. One rule per file, reviewed in a PR, CI runs `sigma check`, conversion and tests. Bump `modified` and note the change in the PR. Move `status` from `experimental` to `test` to `stable` as the rule proves itself in production.
12. Measure after release: alerts per week, true positive ratio, time to triage. Review rules that have not fired in 90 days (is the log still flowing?) and rules with a true positive ratio under about 10 percent.
13. Hand off to `incident-response` when an alert is confirmed malicious or cannot be explained by its owner within the runbook's time limit. Pass the alert, raw events, query used and what was already checked.

## Checklist

Sigma rule:

- `title` says the behavior, not the tool ("AWS CloudTrail Logging Stopped", not "CloudTrail Alert 3").
- `id` is a UUIDv4, unique across the repo. Use `related` with `type: derived` or `obsolete` when replacing a rule.
- `status` is one of `experimental`, `test`, `stable`, `deprecated`, `unsupported`.
- `description`, `references`, `author`, `date` (and `modified` on change) filled in.
- `logsource` uses the standard `product`, `service` or `category` values so pipelines map it (`product: aws`, `service: cloudtrail`).
- `detection` uses named selections and an explicit `condition`. Filters are separate named blocks, not negations buried in a selection.
- Value modifiers used on purpose: `|contains`, `|startswith`, `|endswith`, `|re`, `|cidr`, `|all`. Leading wildcards are expensive on most backends.
- `falsepositives` lists real, specific cases, not "Unknown".
- `level` is one of `informational`, `low`, `medium`, `high`, `critical` and matches impact.
- `tags` include the tactic and technique, lowercase (`attack.defense-evasion`, `attack.t1562.008`).

Native queries:

- Time window and threshold stated and justified (why 50 objects in 10 minutes, not 5).
- Grouped by a stable actor identifier.
- Output includes actor, source IP, count, first and last seen, and target.
- Scheduled interval plus lookback covers ingestion delay, so events are not skipped between runs.

Program:

- Every enabled rule has an owner, runbook link and at least one positive test.
- Allowlist entries have owner, reason and expiry. Expired entries fail CI or open a ticket.
- Log source health is monitored: an alert when a source stops sending is a detection too.
- Coverage table updated when a rule is added, changed or retired.

## Output format

For a rule review:

| Severity | File | Rule | Issue | Fix |
|---|---|---|---|---|
| High | rules/aws/cloudtrail_stopped.yml | AWS CloudTrail Logging Stopped | Only matches `StopLogging`; `DeleteTrail` and `PutEventSelectors` also blind the trail | Add both event names to the selection |
| Medium | rules/aws/root_login.yml | Root Login | `falsepositives: Unknown`, no runbook link | List the break-glass test procedure, add runbook URL |

For a new detection, deliver in this order:

1. The behavior sentence and ATT&CK mapping.
2. The rule (Sigma or native) with metadata.
3. Converted queries for the user's SIEM, with the sigma-cli command used.
4. One positive and one negative sample event.
5. Expected false positives and the tuning plan (filters, allowlist owners, expiry).
6. Runbook outline: what to check first, who owns the account, when to escalate.

## Examples

Bad: vague title, `id` that is not a UUID, wrong field name, no filter, no tags, useless metadata.

```yaml
title: Root Alert
id: 1
status: stable
logsource:
  product: aws
detection:
  selection:
    user: root
  condition: selection
falsepositives:
  - Unknown
level: low
```

Good: specific behavior, real CloudTrail fields, mapped to ATT&CK, false positives that a responder can act on.

```yaml
title: AWS Root Account Console Login
id: 6f1d3c2a-8b4e-4c71-9a35-2e7f0d9b5c18
status: test
description: Detects a console login by the AWS account root user. Root should only be used for break-glass and a few account-level tasks.
references:
  - https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html
author: Platform Security
date: 2026-11-07
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventName: ConsoleLogin
    userIdentity.type: Root
  condition: selection
fields:
  - sourceIPAddress
  - userAgent
  - recipientAccountId
  - additionalEventData.MFAUsed
  - responseElements.ConsoleLogin
falsepositives:
  - Scheduled break-glass test, announced in the change calendar by the cloud platform team
  - Billing or account closure tasks that require root, done under a change ticket
level: high
tags:
  - attack.initial-access
  - attack.privilege-escalation
  - attack.t1078.004
```

Converted for Splunk:

```bash
sigma convert -t splunk --without-pipeline rules/aws/root_console_login.yml
```

More example detections (MFA disabled, new access key, CloudTrail stopped, impossible travel, mass download) and native query patterns are in [references/log-sources.md](references/log-sources.md).
