---
name: secrets-management
description: Find hardcoded secrets in code, config and git history (gitleaks, trufflehog, detect-secrets), plan and run credential rotation after a leak, and move secrets into Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault or KMS-encrypted files (SOPS, Sealed Secrets, External Secrets Operator). Use when the user finds or suspects a leaked key, asks to scan a repo for secrets, set up pre-commit secret scanning, rotate credentials, or replace .env files and plaintext config with a secrets manager.
---

# Secrets Management

Three jobs: find secrets that should not be where they are, rotate anything that leaked, and move the rest into a store with access control, audit logs and rotation. In that order. Rotation comes before cleanup, because a key in git history is already public to anyone with a clone.

## When to use

- A scanner (gitleaks, trufflehog, GitHub secret scanning, GitGuardian) reported a secret.
- Someone committed a key, pasted one in a ticket or log, or suspects a leak.
- The user wants secret scanning in pre-commit hooks or CI.
- Secrets live in `.env` files, `config.yml`, Kubernetes `Secret` manifests in git, Terraform variables, or CI variables, and the team wants a proper store.
- A credential needs a rotation plan or automatic rotation.

Not for: triaging general SAST output (use `sast-dast-triage`), IAM permissions attached to the identity that reads secrets (use `cloud-iam-review`), or active incident coordination beyond the credential itself (use `incident-response`).

## Steps

1. Scan the working tree and history:
   - `gitleaks detect --source . -v --report-format json --report-path gitleaks.json` (full history)
   - `gitleaks detect --no-git -v` (working tree only)
   - `trufflehog git file://. --only-verified --json` (checks if keys are live)
   - `detect-secrets scan --all-files > .secrets.baseline` for a baseline to audit with `detect-secrets audit`.
2. Triage each hit. Real or fake? Test fixtures, example values (`AKIAEXAMPLEEXAMPLE00`, `changeme`), and public keys are not leaks. Record real ones with file, line, commit, author date and secret type. Never print the full secret in the report; show the first 4 characters and the type.
3. For every real secret, assume it is compromised if it was ever pushed to a shared remote, CI log, ticket or chat. Rotate first:
   - Issue a new credential.
   - Deploy it to every consumer.
   - Revoke the old one.
   - Check provider audit logs (CloudTrail, GitHub audit log, Stripe dashboard) for use of the old key between leak and revocation.
4. Only then clean history if needed: `git filter-repo --replace-text replacements.txt` or BFG, then force push and ask everyone to re-clone. Ask the repo owner before rewriting history. Contact GitHub support to purge cached views and PR refs if the repo is public.
5. Remove secrets from code. Replace each with a runtime lookup from the chosen store. Pick the store by platform:
   - AWS: Secrets Manager (rotation via Lambda) or SSM Parameter Store `SecureString`.
   - GCP: Secret Manager. Azure: Key Vault.
   - Multi-cloud or on-prem: HashiCorp Vault (dynamic DB creds, PKI, transit encryption).
   - Kubernetes: External Secrets Operator or the Secrets Store CSI Driver pulling from the store above. For GitOps, SOPS with KMS or age, or Sealed Secrets.
6. Give each workload its own identity to read only its secrets: IRSA or EKS Pod Identity, GKE Workload Identity, Azure Workload Identity, Vault Kubernetes auth with a per-service role and policy.
7. Prefer short-lived credentials over stored ones: OIDC from CI to cloud (GitHub Actions `id-token: write` plus `aws-actions/configure-aws-credentials`), Vault dynamic database secrets, IAM database auth.
8. Add prevention: pre-commit hook, CI scan on every PR, and GitHub push protection.
9. Write the report and the rotation runbook.

## Checklist

Detection and prevention

- `.pre-commit-config.yaml` runs gitleaks (`repo: https://github.com/gitleaks/gitleaks`, hook `gitleaks`) or detect-secrets.
- CI runs `gitleaks detect` or `gitleaks/gitleaks-action` on PRs and fails on new findings.
- `.gitleaks.toml` allowlists only specific test paths or regexes, not whole directories like `src/`.
- GitHub secret scanning and push protection enabled. Custom patterns for internal token formats.
- `.gitignore` covers `.env`, `.env.*`, `*.pem`, `*.key`, `*.tfvars` (except `*.tfvars.example`), `credentials.json`.

Where secrets hide

- `.env`, `docker-compose.yml` `environment:` blocks, `application.properties`, `appsettings.json`, `settings.py`.
- Dockerfile `ENV` and `ARG` (visible in `docker history`). Use BuildKit `--mount=type=secret`.
- Kubernetes `Secret` manifests in git (base64 is encoding, not encryption).
- Terraform state files and `*.tfvars`. Mark outputs `sensitive = true`, store state in an encrypted backend with restricted access.
- CI logs: `set -x`, `echo $TOKEN`, verbose curl. Mask with `::add-mask::` in GitHub Actions.
- Jupyter notebooks output cells, Postman collections, HAR files, crash dumps.
- Frontend bundles: anything in `NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*` ships to every browser.

Store and access

- One secret path per service and environment (`secret/data/prod/billing/db`), not one shared blob.
- Read access scoped per workload identity. Humans get break-glass access with MFA and audit.
- Audit logging on: Vault audit device, CloudTrail data events for Secrets Manager, Key Vault diagnostic logs.
- Rotation scheduled: 90 days or less for static keys, or automatic. Database credentials dynamic where supported.
- KMS keys have rotation enabled and key policies that do not grant `kms:*` to the account root plus everyone.
- App reloads secrets without restart, or restarts cleanly on rotation (Vault Agent template, ESO `refreshInterval`, CSI driver rotation).

A rotation runbook template and provider-specific revocation steps are in [references/rotation-runbook.md](references/rotation-runbook.md).

## Output format

### Findings

| # | Severity | Type | File | Line | Commit | Live? | Exposure | Action |
|---|----------|------|------|------|--------|-------|----------|--------|

Severity:

| Level | Rule |
|-------|------|
| Critical | Verified live production credential with write or admin scope, in a public repo or public log |
| High | Live production credential in a private repo, or any cloud root or org-level key |
| Medium | Non-production credential, or production with read-only narrow scope |
| Low | Revoked or expired credential, or a test value that looks like a secret and trains people to ignore alerts |

Mask secrets in the table: `AKIA****` (AWS access key), `sk_live_****` (Stripe).

### Rotation plan

| Secret | Owner | New credential issued | Consumers updated | Old revoked | Logs checked |

### Migration plan

Short list: each secret, current location, target store path, identity that reads it, code or manifest change.

## Examples

### Bad: secret in code and a Kubernetes Secret in git

```python
# settings.py
AWS_ACCESS_KEY_ID = "AKIAEXAMPLEEXAMPLE00"
AWS_SECRET_ACCESS_KEY = "example/fake/secret/key/do-not-use/0000000"
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: billing-db
data:
  password: ZXhhbXBsZS1wYXNzd29yZA==   # base64 of "example-password"
```

### Good: workload identity and External Secrets Operator

```python
# settings.py: no keys. boto3 picks up the pod's IRSA role automatically.
import boto3, json

def db_password() -> str:
    sm = boto3.client("secretsmanager")
    return json.loads(sm.get_secret_value(SecretId="prod/billing/db")["SecretString"])["password"]
```

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: billing-db
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: billing-db
  data:
    - secretKey: password
      remoteRef:
        key: prod/billing/db
        property: password
```

The git repo holds a pointer, not the value. Access is controlled by the IAM role bound to the `billing` service account.

### Bad vs good: Docker build secret

```dockerfile
# Bad: token stays in image history
ARG NPM_TOKEN
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc && npm ci
```

```dockerfile
# Good: BuildKit secret mount, never written to a layer
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
```

Build with `docker build --secret id=npmrc,src=$HOME/.npmrc .`.
