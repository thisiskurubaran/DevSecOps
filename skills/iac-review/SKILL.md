---
name: iac-review
description: Review Terraform, OpenTofu and CloudFormation for security misconfigurations (public storage, open security groups, missing encryption, disabled logging, unsafe state handling) using Checkov, Trivy config (tfsec) and plan output, and return a findings table with fixed HCL or YAML. Use when the user shares *.tf, *.tfvars, CloudFormation or SAM templates, a terraform plan, or opens a PR that changes infrastructure code.
---

# IaC Review

Catch the misconfigurations that turn into incidents: a public bucket, `0.0.0.0/0` on port 22, an unencrypted database, a state file with secrets in it. Run the scanners, then read the code yourself, because scanners miss intent and context.

## When to use

- The user shares `.tf`, `.tfvars`, `.hcl`, CloudFormation (`.yaml`, `.json`, `template.yml`) or SAM templates.
- The user pastes `terraform plan` output or a `plan.json` and asks if it is safe to apply.
- A PR touches `infra/`, `terraform/`, `modules/`, or `cloudformation/`.
- Someone asks for an "infra review" or "Checkov / tfsec findings" explained and fixed.

Not for: IAM policy documents and trust relationships in depth (use `cloud-iam-review`, though flag obvious `"*"` actions here), Kubernetes YAML or Helm charts (use `k8s-manifest-review`), or writing new OPA/Conftest rules to enforce these checks (use `policy-as-code`).

## Steps

1. Map the change. List providers, modules, and resources being added, changed or destroyed. For a PR, read the diff first, then the surrounding module for context (variables, defaults, locals).
2. Run scanners where possible:
   - `checkov -d . --compact --quiet` (or `-f template.yaml` for one CloudFormation file).
   - `trivy config --severity MEDIUM,HIGH,CRITICAL .` (tfsec checks now live in Trivy).
   - `cfn-lint template.yaml` and `cfn_nag_scan --input-path template.yaml` for CloudFormation.
   - `tflint --recursive` for provider-specific errors.
3. If a plan is available, scan it too: `terraform show -json plan.out > plan.json` then `checkov -f plan.json`. Plans resolve variables and module defaults that static scans guess at.
4. Read each resource against the checklist below. Pay attention to defaults: many providers leave encryption, versioning or logging off unless set.
5. Check exposure. For every network-facing resource, ask who can reach it: security group ingress, NACLs, public IPs, `publicly_accessible`, bucket policies, API gateway auth, load balancer schemes.
6. Check state and secrets. Remote backend with encryption and locking. No secrets in `.tfvars` committed to git, no `default =` on secret variables, `sensitive = true` on outputs that carry secrets.
7. Drop false positives with a reason. If a public bucket is a static website on purpose, say so and suggest an inline skip with justification: `#checkov:skip=CKV_AWS_20:public static site, no PII`.
8. Write fixes as code. Give the corrected HCL or YAML block, not just a description.
9. Rank and report using the output format.

## Checklist

Storage:

- S3: `aws_s3_bucket_public_access_block` with all four flags `true`; SSE with `aws_s3_bucket_server_side_encryption_configuration` (KMS for sensitive data); versioning on; access logging to a separate bucket; bucket policy denies `aws:SecureTransport = false`.
- Azure Storage: `allow_nested_items_to_be_public = false`, `min_tls_version = "TLS1_2"`, `public_network_access_enabled = false` where possible.
- GCS: `uniform_bucket_level_access = true`, `public_access_prevention = "enforced"`, no `allUsers` or `allAuthenticatedUsers` members.

Network:

- No ingress from `0.0.0.0/0` or `::/0` on 22, 3389, database ports (3306, 5432, 1433, 6379, 27017, 9200).
- Default security group restricts all traffic (CKV2_AWS_12).
- VPC flow logs enabled.
- Load balancers: HTTPS listeners with a current TLS policy (`ELBSecurityPolicy-TLS13-1-2-2021-06`), HTTP redirects to HTTPS, `drop_invalid_header_fields = true`.

Compute and data:

- RDS / Cloud SQL / Azure SQL: `storage_encrypted = true`, `publicly_accessible = false`, `deletion_protection = true`, backups retained, IAM auth where supported.
- EC2: IMDSv2 required (`metadata_options { http_tokens = "required" }`), EBS encryption on, no secrets in `user_data`.
- Lambda: no secrets in `environment` (use Secrets Manager or SSM), concurrency limit set for public triggers.
- EKS / GKE / AKS: private API endpoint or restricted `public_access_cidrs`, secrets envelope encryption, control plane logging on.

Logging and keys:

- CloudTrail multi-region with log file validation; GCP audit logs; Azure diagnostic settings.
- KMS keys with `enable_key_rotation = true` and a key policy that does not grant `kms:*` to `*`.

Terraform hygiene:

- Remote backend (`s3` with `encrypt = true` and `use_lockfile = true` or a DynamoDB lock table, `gcs`, `azurerm`).
- Providers and modules version-pinned (`required_providers` with `~>`; module `source` with `?ref=v1.2.3` or registry `version`).
- Secret variables have `sensitive = true` and no default.
- No `local-exec` provisioners that curl and pipe to shell.

CloudFormation:

- `DeletionPolicy: Retain` on stateful resources.
- Parameters for secrets use `NoEcho: true` or dynamic references `{{resolve:secretsmanager:...}}`.
- No inline `AWS::IAM::Policy` with `Action: "*"`.

See [references/checkov-ids.md](references/checkov-ids.md) for the check IDs that map to each item.

## Output format

| Severity | File | Line | Resource | Issue | Fix |
|---|---|---|---|---|---|
| Critical | infra/s3.tf | 14 | aws_s3_bucket.uploads | No public access block, bucket policy allows `s3:GetObject` to `*` | Add `aws_s3_bucket_public_access_block`, remove the `Principal: "*"` statement |
| High | infra/sg.tf | 30 | aws_security_group.db | Ingress 5432 from `0.0.0.0/0` | Restrict to the app security group ID |

After the table:

1. Fixed code blocks for each Critical and High.
2. Scanner summary: tool, version, passed/failed counts, and which findings you marked as false positives with reasons.
3. Anything you could not judge without more context (for example, "is this bucket meant to be public?").

Severity: Critical (data exposed to the internet, secrets in code or state, admin access open), High (missing encryption on sensitive data, management port open, logging off on audit trails), Medium (missing versioning, weak TLS policy, unpinned module), Low (tags, naming, hygiene).

## Examples

Bad: public bucket, no encryption, SSH open to the world.

```hcl
resource "aws_s3_bucket" "uploads" {
  bucket = "example-uploads"
}

resource "aws_s3_bucket_acl" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  acl    = "public-read"
}

resource "aws_security_group_rule" "ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.app.id
}
```

Good: blocked public access, KMS encryption, versioning, SSH replaced by SSM Session Manager.

```hcl
resource "aws_s3_bucket" "uploads" {
  bucket = "example-uploads"
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.uploads.arn
    }
  }
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  versioning_configuration {
    status = "Enabled"
  }
}

# No SSH rule. Instances get the AmazonSSMManagedInstanceCore policy
# and engineers connect with `aws ssm start-session`.
```
