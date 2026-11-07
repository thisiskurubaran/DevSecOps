# Tool notes for CSPM triage

Commands and fields for each posture tool. Flags change between releases, so confirm with `--help` for the installed version.

## Prowler (v4 and later)

```bash
# CIS AWS 3.0, JSON (OCSF) and CSV output
prowler aws --compliance cis_3.0_aws -M json-ocsf csv -o ./prowler-out

# One profile, two regions, failures only
prowler aws --profile prod -f eu-west-1 us-east-1 --status FAIL

# Only some checks or services
prowler aws --checks s3_account_level_public_access_blocks ec2_ebs_default_encryption
prowler aws --services s3 ec2

# Apply a mutelist
prowler aws --mutelist-file mutelist.yaml

# List compliance frameworks and checks
prowler aws --list-compliance
prowler aws --list-checks

# Other clouds
prowler azure --az-cli-auth
prowler gcp
```

Output modes: `csv`, `json-ocsf`, `json-asff` (for Security Hub import), `html`. The compliance run also writes a per-framework CSV with the requirement ID next to each check.

Useful fields in OCSF JSON: `status_code` (PASS, FAIL, MANUAL), `severity`, `metadata.event_code` (the check ID), `resources[].uid` (ARN), `cloud.account.uid`, `cloud.region`, `unmapped.compliance`.

Mutelist sketch, scoped to one account, check, region and resource:

```yaml
Mutelist:
  Accounts:
    "123456789012":
      Checks:
        "s3_bucket_public_access":
          Regions:
            - "eu-west-1"
          Resources:
            - "docs-example-com"
          Description: "Public docs site, no private objects. Owner: docs team. Review by 2027-02-01."
```

Common AWS check IDs:

| Area | Prowler check |
|---|---|
| Account S3 Block Public Access | s3_account_level_public_access_blocks |
| Public bucket | s3_bucket_public_access |
| EBS default encryption | ec2_ebs_default_encryption |
| Public EBS snapshot | ec2_ebs_public_snapshot |
| IMDSv2 on instances | ec2_instance_imdsv2_enabled |
| SSH open to internet | ec2_securitygroup_allow_ingress_from_internet_to_tcp_port_22 |
| RDS publicly accessible | rds_instance_no_public_access |
| Root MFA | iam_root_mfa_enabled |
| CloudTrail multi-region | cloudtrail_multi_region_enabled |
| GuardDuty on | guardduty_is_enabled |
| Access Analyzer on | accessanalyzer_enabled |

## ScoutSuite

```bash
scout aws --profile prod --report-dir ./scout-report
scout azure --cli
scout gcp --user-account
```

The HTML report groups by service and rule with a "flagged items" count. The raw data sits in a `scoutsuite-results` JS file next to the report; strip the leading variable assignment to read it as JSON.

## AWS Security Hub

```bash
# Active failed control findings
aws securityhub get-findings \
  --filters '{"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}],"RecordState":[{"Value":"ACTIVE","Comparison":"EQUALS"}]}' \
  > sechub.json

# Suppress one finding with a note
aws securityhub batch-update-findings \
  --finding-identifiers Id=<finding-id>,ProductArn=<product-arn> \
  --workflow Status=SUPPRESSED \
  --note Text="Accepted by payments team until 2027-02-01",UpdatedBy=payments
```

Findings are in ASFF. Group on `Compliance.SecurityControlId` (for example `S3.1`, `EC2.7`, `EC2.8`) when consolidated control findings are on, otherwise on `GeneratorId`. Use automation rules for repeat suppressions so new findings matching the pattern get the same treatment.

## Microsoft Defender for Cloud

```bash
az security assessment list -o json > defender.json
```

Group on the assessment name and `resourceDetails`. Use exemptions (Mitigated or Waiver) with an expiration date instead of disabling a recommendation for the whole subscription.

## GCP Security Command Center

```bash
gcloud scc findings list organizations/<org-id> --filter='state="ACTIVE"' --format=json > scc.json
```

Group on `finding.category` and `resourceName`. Mute single findings or create mute rules with a filter scoped to the project and category.

## Steampipe and Powerpipe

```bash
powerpipe mod install github.com/turbot/steampipe-mod-aws-compliance
powerpipe benchmark run aws_compliance.benchmark.cis_v300 --export csv
```

Each row carries the control, resource, status (`alarm`, `ok`, `info`, `skip`, `error`) and reason. Triage `alarm` rows; read `error` rows as missing permissions or disabled regions, not as findings.
