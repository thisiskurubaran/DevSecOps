# Checkov IDs for common IaC checks

Use these IDs in findings so readers can look up the rule and add skips with the right ID. IDs can change between releases; confirm with `checkov --list` for your version. Trivy prints its own `AVD-*` ID next to each finding, use that one when the finding came from Trivy.

## AWS

| Check | Checkov |
|---|---|
| S3 public access block on | CKV2_AWS_6 |
| S3 encryption with KMS | CKV_AWS_145 |
| S3 versioning | CKV_AWS_21 |
| S3 access logging | CKV_AWS_18 |
| Security group no 0.0.0.0/0 to 22 | CKV_AWS_24 |
| Security group no 0.0.0.0/0 to 3389 | CKV_AWS_25 |
| Default SG restricts all | CKV2_AWS_12 |
| VPC flow logs | CKV2_AWS_11 |
| RDS encrypted | CKV_AWS_16 |
| RDS not public | CKV_AWS_17 |
| EC2 IMDSv2 required | CKV_AWS_79 |
| EBS encrypted | CKV_AWS_3 |
| CloudTrail log validation | CKV_AWS_36 |
| CloudTrail multi-region | CKV_AWS_67 |
| KMS rotation | CKV_AWS_7 |
| EKS endpoint not public | CKV_AWS_39 |
| ALB drops invalid headers | CKV_AWS_131 |

## Azure

| Check | Checkov |
|---|---|
| Storage min TLS 1.2 | CKV_AZURE_44 |
| Storage no public blob access | CKV_AZURE_190 |
| SQL server no public network | CKV_AZURE_113 |
| Key Vault purge protection | CKV_AZURE_110 |
| NSG no 0.0.0.0/0 to 22 | CKV_AZURE_10 |

## GCP

| Check | Checkov |
|---|---|
| GCS uniform bucket access | CKV_GCP_29 |
| GCS no public access | CKV_GCP_28 |
| Cloud SQL requires SSL | CKV_GCP_6 |
| Firewall no 0.0.0.0/0 to 22 | CKV_GCP_2 |
| GKE private cluster | CKV_GCP_25 |

## Skipping a check with a reason

Terraform:

```hcl
resource "aws_s3_bucket" "site" {
  #checkov:skip=CKV2_AWS_6:public static website, contains no user data
  # For Trivy, add a #trivy:ignore:<AVD-ID> comment with the ID from its output
  bucket = "www-example-com"
}
```

CloudFormation:

```yaml
Resources:
  SiteBucket:
    Type: AWS::S3::Bucket
    Metadata:
      checkov:
        skip:
          - id: CKV_AWS_20
            comment: public static website, contains no user data
```

Every skip needs a comment. A skip without a reason is a finding.
