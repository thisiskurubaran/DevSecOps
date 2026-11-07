---
name: gitops-security
description: Review the security of GitOps setups on Argo CD and Flux: AppProject scoping, argocd-rbac-cm policies, local admin and API server exposure, repo credential scope, ApplicationSet generator risks, auto-sync prune and selfHeal, sync windows, Flux tenant isolation with serviceAccountName and --no-cross-namespace-refs, source verification, SOPS decryption, and config repo controls (branch protection, CODEOWNERS, signed commits, image update automation, drift and audit). Use when the user shares AppProject, Application, ApplicationSet, argocd-cm or argocd-rbac-cm YAML, Flux Kustomization, HelmRelease, GitRepository or OCIRepository objects, asks if their GitOps or multi-tenant Argo CD or Flux setup is safe, or opens a PR touching the config repo or clusters/ directory.
---

# GitOps Security Review

In GitOps, whoever can merge to the config repo can change the cluster. Review three layers: who can write to Git, what the GitOps controller is allowed to apply and where, and who can talk to the controller directly.

## When to use

- The user shares Argo CD objects (`AppProject`, `Application`, `ApplicationSet`) or the `argocd-cm`, `argocd-rbac-cm` or `argocd-cmd-params-cm` ConfigMaps.
- The user shares Flux objects (`Kustomization`, `HelmRelease`, `GitRepository`, `OCIRepository`, `ImageUpdateAutomation`) or the controller flags from a Flux bootstrap.
- The user asks if teams are isolated from each other in a shared Argo CD or Flux install.
- A PR touches the config repo, `clusters/`, `apps/`, `argocd/` or `flux-system/`.
- The user asks how to set up branch protection, CODEOWNERS or commit signing for a deployment repo.

Not for: the Deployments, RBAC and NetworkPolicies being deployed (use `k8s-manifest-review`), chart templates and values (use `helm-review`), signing images and attestations (use `artifact-signing`), CI workflows that build and push (use `pipeline-hardening`), secret storage, vaults and rotation (use `secrets-management`).

## Steps

1. Map the setup: which controller, how many clusters, which repos (app repo vs config repo), and which teams share the install. Draw who can write to each repo and which namespaces each team should own.
2. Collect the objects. For Argo CD: `kubectl -n argocd get appprojects,applications,applicationsets -o yaml`, plus `argocd-cm`, `argocd-rbac-cm`, `argocd-cmd-params-cm` and repository Secrets (labels only, never print the values). For Flux: `flux get all -A`, `kubectl get kustomizations,helmreleases,gitrepositories,ocirepositories -A -o yaml`, and the controller Deployment args in `flux-system`.
3. Argo CD projects: check every `AppProject` against the checklist. Find Applications still in the `default` project: `kubectl -n argocd get applications -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.project}{"\n"}{end}'`.
4. Argo CD access: read `policy.csv` and `policy.default` in `argocd-rbac-cm`, check `admin.enabled` and `accounts.*` in `argocd-cm`, and test a team role with `argocd admin settings rbac can role:team-a sync applications 'team-b/*' --policy-file policy.csv`.
5. ApplicationSets: for each generator, ask who controls its input. A `pullRequest` or `scmProvider` generator takes data from anyone who can open a PR or create a repo. Confirm that input never reaches `project`, `destination` or `source.repoURL`.
6. Flux tenancy: check that every tenant `Kustomization` and `HelmRelease` sets `serviceAccountName`, and that kustomize-controller and helm-controller run with `--no-cross-namespace-refs=true` and `--default-service-account`.
7. Sources: check commit or artifact verification (`signatureKeys` on the AppProject, `.spec.verify` on Flux sources), and that repo credentials are read-only and scoped per repo.
8. Git side: read branch protection or rulesets on the config repo, `CODEOWNERS`, and whether image update automation pushes straight to a protected branch.
9. Drift and audit: confirm OutOfSync and failed syncs alert someone, and that changes made outside Git are detected and reverted or reported.
10. Write findings with the exact object, field and fix. See [references/controller-settings.md](references/controller-settings.md) for the keys and flags.

## Checklist

Argo CD AppProject:

- Teams never use the `default` project. Lock it down: empty `sourceRepos` and `destinations`, or delete and recreate it with nothing allowed.
- `sourceRepos` lists exact repo URLs, not `'*'`.
- `destinations` names the team's clusters and namespaces. No `namespace: '*'` and no `server: '*'` for a team project.
- `clusterResourceWhitelist` is empty for team projects, or lists only the kinds they need. Teams should not create `ClusterRole`, `ClusterRoleBinding`, `CustomResourceDefinition` or `Namespace` by default.
- `namespaceResourceBlacklist` blocks `ResourceQuota`, `LimitRange` and `NetworkPolicy` if the platform team owns those.
- Project `roles` give CI tokens only the verbs they need (`sync`, `get`) on that project's applications.
- `signatureKeys` is set when commits are GPG signed, so Argo CD refuses unsigned or unknown-key revisions.

Argo CD RBAC and accounts:

- `policy.default` is empty or `role:readonly`, never `role:admin`.
- SSO groups map to roles with `g, <group>, role:<name>` lines. Admin goes to one small platform group.
- No `p, role:..., *, *, */*, allow` except the platform admin role.
- `exec` (`applications, exec`) is granted only to people who would have `kubectl exec` anyway.
- `admin.enabled: "false"` in `argocd-cm` once SSO works. Delete `argocd-initial-admin-secret` after first login.
- Local `accounts.<name>` are for automation only, with `apiKey` capability and no `login`.
- `users.anonymous.enabled` is not `"true"`.

Argo CD API server:

- Not exposed to the internet. Put it behind SSO, a VPN or an IP allowlist.
- TLS on the server or terminated at an ingress that re-encrypts. `server.insecure: "true"` only behind a TLS-terminating proxy you control.
- `server.disable.auth` is never `"true"`.
- Tokens for CI are project role tokens with an expiry, not an admin account token.

Repo credentials:

- Read-only deploy keys or tokens. Argo CD and Flux only need to read, except image update automation.
- One credential per repo, or a `repo-creds` template scoped to a narrow URL prefix, not one org-wide token.
- In multi-tenant Argo CD, repository Secrets set `project:` so other projects cannot use them.

ApplicationSets:

- Only platform admins can create or edit ApplicationSets.
- `project` in the template is a fixed string, never a generator parameter.
- `pullRequest` and `scmProvider` generators: templated values only go into names, labels and image tags, never `destination.server`, `destination.namespace` or `repoURL`. Restrict SCM providers with `applicationsetcontroller.allowed.scm.providers`, or turn them off with `applicationsetcontroller.enable.scm.providers: "false"`.
- `syncPolicy.applicationsSync: create-update` or `create-only` where deleting the ApplicationSet must not delete running apps. `preserveResourcesOnDeletion: true` for the same reason.

Sync policy:

- `automated.prune: true` deletes anything removed from Git. Fine for stateless apps; protect stateful resources with the `argocd.argoproj.io/sync-options: Prune=false` annotation.
- `automated.selfHeal: true` reverts manual changes, which stops drift but also undoes emergency hotfixes. Document the break-glass path.
- `allowEmpty: false` (the default), so an empty commit cannot prune a whole app.
- Production projects have `syncWindows` with `kind: deny` for freeze periods. Set `manualSync: false` on a deny window if even manual syncs must stop.
- Notifications on `on-sync-failed` and `on-health-degraded` reach a channel someone reads.

Flux:

- Tenant `Kustomization` and `HelmRelease` set `spec.serviceAccountName` to an account bound only in the tenant namespace. Without it, the controller applies with its own cluster-admin permissions.
- kustomize-controller and helm-controller: `--no-cross-namespace-refs=true` and `--default-service-account=<name>` so a missing `serviceAccountName` fails closed. kustomize-controller also `--no-remote-bases=true`.
- `GitRepository.spec.verify` with `mode` and a `secretRef` holding OpenPGP public keys when commits are signed.
- `OCIRepository.spec.verify.provider: cosign` with a `secretRef` to the public key, or `matchOIDCIdentity` for keyless.
- SOPS: `spec.decryption.provider: sops` with a `secretRef` to the age key, or KMS through workload identity. `.sops.yaml` uses `encrypted_regex: ^(data|stringData)$` so metadata stays readable.

Git side:

- Branch protection or a ruleset on the config repo's default branch: required pull request reviews, no direct pushes, no force pushes, admins included.
- `CODEOWNERS` per environment, e.g. `/clusters/prod/ @example-org/platform`, with "Require review from Code Owners" turned on.
- Signed commits required on the protected branch when the controller verifies signatures.
- App repo and config repo are separate. App developers can merge app code without being able to change prod config.
- Image update automation pushes to a separate branch and opens a PR for prod, or is limited by an `ImagePolicy` semver range. A write deploy key for it is scoped to the config repo only.

Drift and audit:

- `argocd app diff` or `flux diff kustomization` in PR checks shows what a merge will change.
- Alerts on OutOfSync that lasts, not only on sync failures.
- Git history plus Argo CD server logs or Flux events answer "who changed what and when". Ship them off the cluster.

## Output format

| Severity | Object | Field | Area | Issue | Fix |
|---|---|---|---|---|---|
| Critical | ConfigMap/argocd-rbac-cm | policy.default | RBAC | `role:admin` for every logged-in user | Set `role:readonly`, map admin to one SSO group |
| Critical | ApplicationSet/previews | template.spec.destination.namespace | ApplicationSet | Namespace templated from PR branch name | Fix namespace per project, use params only in names |
| High | AppProject/team-a | sourceRepos, destinations | Project scope | `'*'` repos and namespaces | List exact repo URLs and team namespaces |
| High | Kustomization/team-a-apps | spec.serviceAccountName | Flux tenancy | Unset, applies as cluster-admin | Set tenant SA, add `--default-service-account` |
| Medium | Repo github.com/example-org/config | branch protection | Git | Direct pushes to main allowed | Require PR review and CODEOWNERS review |
| Low | AppProject/prod | syncWindows | Change control | No freeze window | Add deny window for release freezes |

After the table:

1. Patches for Critical and High findings as YAML.
2. Tenancy map: each team, its project or service account, allowed repos, clusters and namespaces.
3. Git controls status: branch protection, CODEOWNERS, signed commits, who can merge to prod paths.

Severity: Critical (any user or PR author can deploy anywhere or gain cluster-admin), High (team can escape its namespace or repo scope, local admin enabled and exposed, unverified sources for prod), Medium (missing Git controls, broad repo credentials, prune without protection on stateful apps), Low (missing notifications, sync windows, audit gaps).

## Examples

Bad: team project open to every repo and namespace, admin for everyone.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: team-a
  namespace: argocd
spec:
  sourceRepos: ['*']
  destinations:
    - server: '*'
      namespace: '*'
  clusterResourceWhitelist:
    - group: '*'
      kind: '*'
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:admin
```

Good: exact repo, team namespaces only, no cluster-scoped kinds, SSO group mapping.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: team-a
  namespace: argocd
spec:
  sourceRepos:
    - https://github.com/example-org/team-a-config.git
  destinations:
    - server: https://kubernetes.default.svc
      namespace: team-a-*
  clusterResourceWhitelist: []
  namespaceResourceBlacklist:
    - group: ''
      kind: ResourceQuota
    - group: networking.k8s.io
      kind: NetworkPolicy
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  scopes: '[groups]'
  policy.csv: |
    p, role:team-a, applications, *, team-a/*, allow
    g, example-org:team-a, role:team-a
    g, example-org:platform, role:admin
```

Good Flux tenant: impersonation, verified source, SOPS decryption.

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: team-a-apps
  namespace: team-a
spec:
  interval: 10m
  path: ./deploy/prod
  prune: true
  serviceAccountName: team-a-reconciler
  sourceRef:
    kind: GitRepository
    name: team-a-config
  decryption:
    provider: sops
    secretRef:
      name: sops-age
---
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: team-a-config
  namespace: team-a
spec:
  interval: 5m
  url: https://github.com/example-org/team-a-config.git
  ref:
    branch: main
  secretRef:
    name: team-a-readonly
  verify:
    mode: HEAD
    secretRef:
      name: team-a-gpg-keys
```
