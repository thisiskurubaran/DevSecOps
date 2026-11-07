---
name: cspm-triage
description: Triage cloud security posture findings from Prowler, ScoutSuite, AWS Security Hub, Microsoft Defender for Cloud, GCP Security Command Center or Steampipe/Powerpipe benchmarks into a ranked fix plan, grouped by control and resource, ranked by exposure instead of raw severity, with IaC drift calls, suppressions with expiry, account-level quick wins and CIS mapping. Use when the user shares CSPM or posture scan output (CSV, JSON, OCSF, ASFF), a Security Hub or Defender export, a failing CIS benchmark run, or asks which cloud findings to fix first.
---

# CSPM Triage

A posture scan of one AWS account often returns hundreds of failed checks. Most of them collapse into a few controls, a handful of account-level settings, and a short list of resources that are actually exposed. This skill turns the raw export into a fix plan the team can work through: what to fix, where to fix it (code or console), who owns it, and how long it takes.

## When to use

- The user shares output from Prowler, ScoutSuite, Security Hub, Defender for Cloud, Security Command Center, or a Steampipe/Powerpipe benchmark (CSV, JSON, OCSF, ASFF, HTML report).
- A CIS Benchmark run failed and someone asks what to fix first.
- Security Hub or Defender shows a low secure score and the team wants a plan, not a list.
- The user wants to suppress or accept findings and needs the right scope and an expiry date.

Not for: reviewing Terraform or CloudFormation code before it is applied (use `iac-review`), deep analysis of IAM policies, trust relationships and permission boundaries (use `cloud-iam-review`), tracking remediation SLAs and finding age across scans over time (use `vuln-management`), or code scanner output such as SARIF from Semgrep or CodeQL (use `sast-dast-triage`).

## Steps

1. Get the raw export, not a dashboard screenshot. Ask which accounts, subscriptions or projects and which regions were scanned. Common commands:
   - `prowler aws --compliance cis_3.0_aws -M json-ocsf csv -o ./prowler-out`
   - `aws securityhub get-findings --filters '{"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}],"RecordState":[{"Value":"ACTIVE","Comparison":"EQUALS"}]}' > sechub.json`
   - `powerpipe benchmark run aws_compliance.benchmark.cis_v300 --export csv`
   - More in [references/tool-notes.md](references/tool-notes.md).
2. Keep only failures. Drop PASS, MANUAL and INFO rows, and Security Hub findings with `RecordState` `ARCHIVED`. Record the counts so the summary shows what was filtered.
3. Group by control, then by resource. One control (for example "S3 bucket allows public read") failing on 40 buckets is one work item with 40 resources, not 40 items. Deduplicate across tools: Security Hub often holds the same Config rule result that Prowler reports.
4. Pull out account-level quick wins first. A single setting often clears dozens of findings and blocks repeats (see Checklist). These usually go to the top of the plan regardless of severity.
5. Rank the rest by exposure, not by the tool's severity field. For each resource group ask:
   - Internet-facing: public IP, public bucket or snapshot, `0.0.0.0/0` ingress, public load balancer, public API endpoint.
   - Data sensitivity: does it hold customer data, credentials, backups, logs with PII? Check tags (`data-classification`), naming, and ask when unclear.
   - Blast radius: production vs sandbox, shared services account, org management account, a role or key that many workloads use.
   A "high" unencrypted volume in a sandbox ranks below a "medium" public snapshot of a production database.
6. Check drift against IaC for every resource you plan to change:
   - Look for IaC tags (`managed-by`, `terraform`, `aws:cloudformation:stack-name`), then confirm with `terraform state list | grep <name>` in the right workspace.
   - Managed by Terraform or CloudFormation: fix in code and apply. A console fix gets reverted on the next apply, or the next `terraform plan -refresh-only` shows it as drift.
   - Not in any state (ClickOps): decide import or delete. Import with a Terraform `import` block if the resource is needed, delete it if nobody owns it. Find the creator with `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<name>` (90 days of management events).
7. Separate false positives and accepted risks. A false positive needs a reason someone can check ("bucket serves the public docs site behind CloudFront, no private objects"). An accepted risk needs an owner, a reason and an expiry date, usually 90 days or less. Scope every suppression to the check and the resource, never the whole check across all accounts.
8. Map each control to the CIS Benchmark requirement the tool reports. Prowler `--compliance` output and Security Hub CIS findings carry the requirement ID; copy it from the output instead of guessing numbers.
9. Assign an owner and effort to each work item. Owner is a team, taken from account ownership or resource tags. Effort: S (one setting or one PR, under an hour), M (a few PRs or a maintenance window), L (redesign, migration, or coordination across teams).
10. Write the fix plan in the output format. Include the exact command or IaC change for each quick win and each Critical or High item.

## Checklist

Account-level quick wins (AWS, set once per account and region):

- S3 Block Public Access at the account level: `aws s3control put-public-access-block --account-id 123456789012 --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true`. Terraform: `aws_s3_account_public_access_block`. Check first that no bucket is meant to be public.
- EBS encryption by default, per region: `aws ec2 enable-ebs-encryption-by-default --region eu-west-1`. Terraform: `aws_ebs_encryption_by_default`. Only affects new volumes; existing ones need snapshot, copy encrypted, and swap.
- IMDSv2 as the account default for new instances, per region: `aws ec2 modify-instance-metadata-defaults --http-tokens required --region eu-west-1`. Terraform: `aws_ec2_instance_metadata_defaults`. Existing instances still need `modify-instance-metadata-options`, and old SDKs on them may need an upgrade first.
- GuardDuty, Security Hub and IAM Access Analyzer enabled in every used region, ideally through a delegated admin account in the organization.
- CloudTrail organization trail, multi-region, with log file validation.

Equivalent tenant or org level settings elsewhere: GCP organization policies (for example `constraints/storage.publicAccessPrevention`, `constraints/compute.requireOsLogin`) and Azure Policy assignments at management group scope.

Signs a finding ranks high:

- Public read or write on storage, or a public snapshot or AMI.
- Management ports (22, 3389) or database ports open to `0.0.0.0/0`.
- Root account without MFA, or root access keys present.
- Audit logging disabled (CloudTrail, Activity Log export, Cloud Audit Logs).
- Resource sits in production or a shared account and holds sensitive data.

Common false positives and noise:

- Buckets that serve a public website on purpose, with a documented reason.
- Checks for regions the org never uses. Fix with an SCP that denies those regions, then exclude them from scans, rather than suppressing per finding.
- Duplicate findings for the same control from two tools or two standards in Security Hub. Turn on consolidated control findings.
- Default VPCs in unused regions: delete them or accept, do not triage each subnet.

Suppression formats (always include reason, owner and expiry):

- Prowler: mutelist YAML passed with `--mutelist-file`, scoped by account, check, region and resource, with a `Description` field for the reason.
- Security Hub: `aws securityhub batch-update-findings` with `Workflow={Status=SUPPRESSED}` and a `Note`, or an automation rule for repeat patterns.
- Defender for Cloud: exempt the assessment with category "Mitigated" or "Waiver" and an expiration date.
- Security Command Center: mute the finding or create a mute rule with a filter.
- Track the expiry somewhere a person will see it (ticket with a due date). Most tools do not expire suppressions on their own.

## Output format

Start with a summary line: accounts and regions scanned, total failed findings, controls after grouping, quick wins, false positives, accepted risks.

### Fix plan (ranked)

| Rank | Control / check | CIS | Resources | Exposure | Managed by | Fix | Owner | Effort |
|---|---|---|---|---|---|---|---|---|
| 1 | s3_account_level_public_access_blocks | from output | 3 accounts | Internet, prod data | Terraform (org-baseline) | Add `aws_s3_account_public_access_block` to baseline module | Platform | S |
| 2 | ec2_securitygroup_allow_ingress_from_internet_to_tcp_port_22 | from output | sg-0abc in prod | Internet, prod | ClickOps | Import into Terraform, replace SSH with SSM Session Manager | Payments | M |

Exposure uses: Internet, Internal, Isolated, plus data class and environment. "Managed by" is Terraform, CloudFormation, other IaC, or ClickOps.

### Quick wins

Each account-level setting with the exact command or IaC resource and the number of findings it clears.

### False positives and accepted risks

| Check | Resource | Type | Reason | Owner | Expiry | Suppression |
|---|---|---|---|---|---|---|

### ClickOps resources

Resources not in any IaC state, with the proposed action (import or delete) and who created them if CloudTrail shows it.

### Open questions

Anything you could not rank without context, such as data classification or whether a bucket is meant to be public.

## Examples

### Bad triage

> Prowler found 312 failures, 41 critical. I sorted by severity and fixed the critical ones in the console, starting with the unencrypted EBS volumes.

Sorting by severity puts sandbox volumes ahead of a public prod snapshot. Console fixes on Terraform-managed resources get reverted on the next apply. Nothing stops new unencrypted volumes from appearing tomorrow.

### Good triage

312 failures in 123456789012 collapse into 27 controls. Top of the plan:

1. `ec2_ebs_public_snapshot`: 1 snapshot of the orders database, shared publicly. Internet plus customer data plus prod, so it ranks first on exposure even though the tool did not mark it critical. Created from the console, not in any state. Action: remove the public share now, delete after the owner confirms. Owner: Orders, effort S.
2. Account-level defaults, Platform team, effort S: `aws ec2 enable-ebs-encryption-by-default` and `aws ec2 modify-instance-metadata-defaults --http-tokens required` in the two used regions, added to the `org-baseline` Terraform module so they do not drift. This stops new unencrypted volumes and IMDSv1 instances; existing volumes and instances are separate items further down.
3. `s3_bucket_public_access` on `docs-example-com`: false positive. The bucket serves the public docs site and holds no private objects. Muted in the Prowler mutelist with that reason, owner Docs, expiry 2027-02-01.
4. 140 findings from regions the org does not use: proposed an SCP that denies those regions and excluded them from the scan, instead of muting each finding.
