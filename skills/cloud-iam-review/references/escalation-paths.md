# Privilege escalation paths

A principal holding any of these combinations can usually become admin or act as a stronger identity. Treat them as Critical unless the resource scope makes the path impossible.

## AWS

| Permissions | Why it escalates |
|---|---|
| `iam:CreatePolicyVersion` | Write a new default version of an attached policy with `"Action": "*"` |
| `iam:SetDefaultPolicyVersion` | Switch to an older, broader version of a policy |
| `iam:AttachUserPolicy`, `iam:AttachRolePolicy`, `iam:AttachGroupPolicy` | Attach `AdministratorAccess` to self |
| `iam:PutUserPolicy`, `iam:PutRolePolicy`, `iam:PutGroupPolicy` | Add an inline admin policy to self |
| `iam:AddUserToGroup` | Join an admin group |
| `iam:CreateAccessKey` on other users | Mint keys for a stronger user |
| `iam:CreateLoginProfile`, `iam:UpdateLoginProfile` | Set a console password for a stronger user |
| `iam:UpdateAssumeRolePolicy` + `sts:AssumeRole` | Edit a strong role's trust to allow self, then assume it |
| `iam:PassRole` + `ec2:RunInstances` | Launch an instance with a strong instance profile and read its credentials |
| `iam:PassRole` + `lambda:CreateFunction` + `lambda:InvokeFunction` | Run code as a strong role |
| `iam:PassRole` + `cloudformation:CreateStack` | Stack creates resources as a strong role |
| `iam:PassRole` + `glue:CreateDevEndpoint` or `glue:CreateJob` | Run code as a strong role |
| `lambda:UpdateFunctionCode` on a function with a strong role | Replace its code |
| `ssm:SendCommand` or `ssm:StartSession` on instances with strong profiles | Run commands as that instance role |
| `sts:AssumeRole` on `*` | Assume any role whose trust allows the account |

Check a role with tools like PMapper (`pmapper graph create`, `pmapper query 'preset privesc *'`) or Cloudsplaining (`cloudsplaining scan --input-file account-auth.json`).

## GCP

| Permissions | Why it escalates |
|---|---|
| `iam.serviceAccounts.actAs` (`roles/iam.serviceAccountUser`) | Deploy resources that run as a stronger service account |
| `iam.serviceAccounts.getAccessToken` (`roles/iam.serviceAccountTokenCreator`) | Mint tokens for a stronger service account |
| `iam.serviceAccountKeys.create` | Create a long-lived key for a stronger service account |
| `resourcemanager.projects.setIamPolicy` | Grant self `roles/owner` |
| `iam.roles.update` on a custom role you hold | Add permissions to your own role |
| `cloudfunctions.functions.create` or `run.services.create` + `actAs` | Run code as a stronger service account |
| `compute.instances.setMetadata` | Add SSH keys or startup scripts to a VM with a strong service account |
| `deploymentmanager.deployments.create` | Deploys run as the project's Google APIs service account, often with editor |

## Azure

| Permissions | Why it escalates |
|---|---|
| `Microsoft.Authorization/roleAssignments/write` | Assign Owner to self |
| `Microsoft.Authorization/roleDefinitions/write` | Broaden a custom role you hold |
| `Microsoft.Compute/virtualMachines/runCommand/action` | Run commands on a VM with a managed identity |
| `Microsoft.Web/sites/config/write` or publish rights on an app with a managed identity | Deploy code that uses that identity |
| `Microsoft.ManagedIdentity/userAssignedIdentities/assign/action` | Attach a stronger identity to a resource you control |
| `Microsoft.KeyVault/vaults/write` | Change the vault access policy to read secrets |
| Entra ID: Application Administrator or owner of an app with high Graph permissions | Add a credential to the app and act as it |

## How to report a path

Write the path as steps, so the reader can see it is real:

1. `role/ci-build` has `iam:PassRole` on `*` and `lambda:CreateFunction`.
2. `role/ops-admin` trusts `lambda.amazonaws.com` and has `AdministratorAccess`.
3. So `ci-build` can create a Lambda with `ops-admin`, invoke it, and run any API call as admin.

Then give the fix that breaks the chain at the cheapest point (usually scoping `iam:PassRole`).
