# Control mapping for common policies

Use this as a starting point, not as audit evidence. Control numbering follows SOC 2 Trust Services Criteria (2017, revised points of focus 2022), ISO/IEC 27001:2022 Annex A, and PCI DSS v4.0. Confirm the exact IDs with your GRC team, since auditors may scope controls differently.

A policy rarely satisfies a control on its own. It is evidence for the technical part. The control usually also needs a process (review, approval, training) that a policy cannot show.

## Cloud and IaC (conftest on Terraform plans)

| Policy | SOC 2 | ISO 27001:2022 | PCI DSS v4.0 |
|---|---|---|---|
| S3 / blob storage blocks public access | CC6.1, CC6.6 | A.8.3, A.8.20 | 1.4.1, 1.3.1 |
| Encryption at rest on storage, DB, volumes (KMS key set) | CC6.1, CC6.7 | A.8.24 | 3.5.1 |
| TLS 1.2+ on load balancers and endpoints | CC6.7 | A.8.24, A.8.20 | 4.2.1 |
| Security groups: no 0.0.0.0/0 on 22, 3389, DB ports | CC6.6 | A.8.20, A.8.22 | 1.3.1, 1.3.2 |
| Logging enabled (CloudTrail, flow logs, access logs) | CC7.2 | A.8.15, A.8.16 | 10.2.1 |
| Log retention at least 1 year | CC7.2 | A.8.15 | 10.5.1 |
| No IAM policies with `"Action": "*"` on `"Resource": "*"` | CC6.1, CC6.3 | A.5.15, A.8.2 | 7.2.1, 7.2.2 |
| Required tags (owner, data-classification) | CC2.1 | A.5.9, A.5.12 | 12.5.1 |
| Backups enabled with retention set | A1.2 | A.8.13 | 12.10.1 (supports) |
| Databases not publicly accessible | CC6.6 | A.8.20 | 1.4.4 |

## Kubernetes admission (Kyverno or Gatekeeper)

| Policy | SOC 2 | ISO 27001:2022 | PCI DSS v4.0 |
|---|---|---|---|
| runAsNonRoot, no privileged, drop ALL capabilities | CC6.8 | A.8.9 | 2.2.1, 2.2.5 |
| Images only from approved registries | CC6.8, CC8.1 | A.8.19 | 6.3.2 |
| Images signed (Kyverno `verifyImages` with cosign) | CC8.1 | A.8.28, A.8.32 | 6.3.2 |
| No `:latest` tag, digest pinned | CC8.1 | A.8.32 | 6.5.1 |
| Resource requests and limits set | A1.1 | A.8.6 | n/a |
| NetworkPolicy present per namespace | CC6.6 | A.8.22 | 1.2.1, 1.3.1 |
| No hostPath, hostNetwork, hostPID | CC6.8 | A.8.9 | 2.2.1 |
| Secrets not in env from literal ConfigMaps | CC6.1 | A.8.24 | 3.6.1, 8.3.2 |

## Pipeline and repo

| Policy | SOC 2 | ISO 27001:2022 | PCI DSS v4.0 |
|---|---|---|---|
| Branch protection with required reviews | CC8.1 | A.8.32 | 6.5.1, 6.5.2 |
| Secret scanning passes before merge | CC6.1 | A.8.4 | 6.2.4 |
| SAST and SCA gates on PRs | CC7.1, CC8.1 | A.8.28, A.8.8 | 6.2.4, 6.3.1 |
| GitHub Actions pinned to commit SHA | CC8.1 | A.8.30 | 6.3.2 |

## Metadata convention

Put the mapping in the policy so a script can build the table:

Rego (OPA METADATA annotation):

```rego
# METADATA
# custom:
#   id: K8S-004
#   severity: high
#   controls: ["SOC2:CC6.8", "ISO27001:A.8.9", "PCI:2.2.1"]
```

Kyverno:

```yaml
metadata:
  annotations:
    policies.kyverno.io/severity: high
    example.com/controls: "SOC2:CC6.8, ISO27001:A.8.9, PCI:2.2.1"
```

Pull them out with `opa inspect -a -f json policy/` for Rego, or `yq '.metadata.annotations' policies/*.yaml` for Kyverno.
