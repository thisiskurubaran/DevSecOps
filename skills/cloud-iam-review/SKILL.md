---
name: cloud-iam-review
description: Review AWS IAM, GCP IAM and Azure RBAC for over-privileged roles, wildcard actions, risky trust policies, privilege escalation paths and long-lived keys, then propose least-privilege replacements based on actual usage (Access Analyzer, IAM Recommender, last-accessed data). Use when the user shares an IAM policy JSON, role trust policy, gcloud or az role binding, Terraform IAM resources, or asks whether a role or service account has too much access.
---

# Cloud IAM Review

Find identities that can do more than their job needs, and shrink them to what they actually use. Read every policy as an attacker would: what is the worst thing this principal can do, and who can become this principal.

## When to use

- The user shares an AWS IAM policy document, a role trust policy, an SCP, or a permission boundary.
- The user shares GCP `bindings` (from `gcloud projects get-iam-policy`), custom role definitions, or Azure role assignments and definitions.
- Terraform or CloudFormation adds `aws_iam_*`, `google_project_iam_*`, `azurerm_role_assignment`, or `AWS::IAM::*` resources.
- Someone asks "is this role too broad", "what can this service account do", or wants least privilege for a CI role, Lambda, or workload identity.

Not for: general IaC misconfigurations like public buckets or open ports (use `iac-review`), Kubernetes RBAC `Role` and `ClusterRole` objects (use `k8s-manifest-review`), or rotating leaked access keys (use `secrets-management`). Writing org-wide guardrails as code goes to `policy-as-code`.

## Steps

1. Identify the principal and its purpose. What runs as this identity (a Lambda, a CI job, a human group) and what does it need to touch? If unknown, ask.
2. Collect every policy that applies. AWS: identity policies (inline and managed), permission boundary, SCPs, resource policies on the targets, session policies. GCP: bindings at org, folder, project and resource level (inherited). Azure: assignments at management group, subscription, resource group and resource scope.
3. Run analyzers where possible:
   - AWS: `aws accessanalyzer validate-policy --policy-type IDENTITY_POLICY --policy-document file://policy.json`, and `checkov` or `parliament` on policy JSON.
   - AWS usage: `aws iam generate-service-last-accessed-details --arn <role-arn>` then `get-service-last-accessed-details`; Access Analyzer unused access findings; policy generation from CloudTrail.
   - GCP: `gcloud recommender recommendations list --recommender=google.iam.policy.Recommender --project=<id> --location=global`.
   - Azure: `az role assignment list --assignee <id> --all` and Entra ID access reviews.
4. Flag wildcards and admin grants: `"Action": "*"`, `"Resource": "*"` with write actions, `service:*`, `AdministratorAccess`, `roles/owner`, `roles/editor`, Azure `Owner` and `Contributor` at subscription scope.
5. Look for privilege escalation paths. A principal that can change its own permissions or pass a stronger role is effectively admin. See [references/escalation-paths.md](references/escalation-paths.md).
6. Review trust. AWS trust policies: who can `sts:AssumeRole`, is there an `ExternalId` for third parties, are OIDC trusts pinned with `sub` and `aud` conditions. GCP: who has `iam.serviceAccountUser` or `iam.serviceAccountTokenCreator` on the service account. Azure: federated credential subject.
7. Check credentials. Long-lived access keys older than 90 days, GCP service account keys (`gcloud iam service-accounts keys list`), Azure client secrets. Prefer OIDC federation, instance roles, workload identity, managed identities.
8. Draft the least-privilege replacement. Scope actions to what last-accessed data shows, resources to specific ARNs or resource names, and add conditions (`aws:SourceVpce`, `aws:PrincipalOrgID`, `aws:RequestedRegion`, IAM Conditions in GCP).
9. Report findings with the replacement policy, and note what to verify after rollout (watch for `AccessDenied` in CloudTrail or audit logs for a week).

## Checklist

Actions and resources:

- No `"Action": "*"` or `"NotAction"` with `"Effect": "Allow"`.
- No `service:*` on production identities (`s3:*`, `iam:*`, `kms:*`, `ec2:*`).
- Write actions scoped to specific ARNs, not `"Resource": "*"`.
- `kms:Decrypt` scoped to specific key ARNs and ideally `kms:ViaService`.
- GCP: no basic roles (`roles/owner`, `roles/editor`, `roles/viewer`) on service accounts; use predefined or custom roles.
- Azure: no `Owner` or `User Access Administrator` for workloads; custom roles with explicit `actions` and `dataActions`.

Escalation:

- No `iam:PassRole` with `"Resource": "*"`. Scope it and add `iam:PassedToService`.
- No `iam:CreatePolicyVersion`, `iam:AttachRolePolicy`, `iam:PutRolePolicy`, `iam:UpdateAssumeRolePolicy` on self or broader roles.
- GCP: no `iam.serviceAccounts.actAs`, `getAccessToken`, or `setIamPolicy` granted broadly.
- Azure: no `Microsoft.Authorization/roleAssignments/write` for workloads.

Trust:

- AWS trust policy `Principal` is a specific account or role, not `"AWS": "*"`.
- Third-party roles require `sts:ExternalId`.
- GitHub OIDC trust has `token.actions.githubusercontent.com:aud = sts.amazonaws.com` and a `sub` condition like `repo:org/app:ref:refs/heads/main`, never `repo:org/*` with `StringLike` on a deploy role.
- Cross-account access restricted with `aws:PrincipalOrgID`.

Credentials and hygiene:

- No IAM users for workloads. Humans through SSO (IAM Identity Center, Google Workspace, Entra ID) with MFA.
- Root account has MFA and no access keys.
- Access keys and SA keys older than 90 days flagged; unused for 90 days removed.
- Permission boundaries on roles that developers can create.
- One role per workload, not a shared "app-role" for every service.

## Output format

| Severity | File | Line | Principal | Issue | Fix |
|---|---|---|---|---|---|
| Critical | iam/ci.json | 6 | role/gha-deploy | `iam:PassRole` on `*` plus `lambda:CreateFunction` allows running code as any role | Scope `PassRole` to `arn:aws:iam::123456789012:role/app-lambda` with `iam:PassedToService` |
| High | infra/iam.tf | 40 | sa/batch@example-proj | `roles/editor` on project | Custom role with `storage.objects.get`, `storage.objects.create` on one bucket |

After the table:

1. The replacement policy or binding, ready to apply.
2. Evidence used: last-accessed report, Recommender output, CloudTrail queries.
3. Rollout notes: what might break, which logs to watch, how to roll back.

Severity: Critical (admin or escalation to admin, public or any-account trust, unpinned OIDC trust on a deploy role), High (service wildcard on prod, basic roles, keys older than 90 days with write access), Medium (read-wide access to data, missing conditions), Low (unused permissions with no data access, naming).

## Examples

Bad: wildcard S3, unscoped PassRole, OIDC trust open to every repo in the org.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": "s3:*", "Resource": "*" },
    { "Effect": "Allow", "Action": ["iam:PassRole", "lambda:*"], "Resource": "*" }
  ]
}
```

```json
{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringLike": { "token.actions.githubusercontent.com:sub": "repo:example-org/*" }
  }
}
```

Good: actions from last-accessed data, one bucket prefix, one passable role, trust pinned to repo and branch.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::example-artifacts/app/*"
    },
    {
      "Effect": "Allow",
      "Action": ["lambda:UpdateFunctionCode", "lambda:GetFunction"],
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:app-api"
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::123456789012:role/app-api-lambda",
      "Condition": { "StringEquals": { "iam:PassedToService": "lambda.amazonaws.com" } }
    }
  ]
}
```

```json
{
  "Effect": "Allow",
  "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:example-org/app:ref:refs/heads/main"
    }
  }
}
```
