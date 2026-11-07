# Argo CD and Flux security settings

Keys and flags this skill checks. Defaults change between releases, so confirm against the docs for the version the user runs and note that version in the report.

## Argo CD

| Where | Key | Secure value | Why |
|---|---|---|---|
| `argocd-cm` | `admin.enabled` | `"false"` after SSO works | Removes the local admin login |
| `argocd-cm` | `users.anonymous.enabled` | unset or `"false"` | Anonymous users get `policy.default` |
| `argocd-cm` | `accounts.<name>` | `apiKey` only | Automation accounts should not log in to the UI |
| `argocd-cm` | `exec.enabled` | `"false"` unless needed | Web terminal into pods |
| `argocd-rbac-cm` | `policy.default` | `role:readonly` or empty | Applies to every authenticated user |
| `argocd-rbac-cm` | `policy.csv` | `p` and `g` lines per team | Maps SSO groups to scoped roles |
| `argocd-rbac-cm` | `scopes` | `[groups]` | Which OIDC claim the `g` lines match |
| `argocd-cmd-params-cm` | `server.insecure` | `"false"` unless TLS ends at a proxy you control | Serves the API without TLS |
| `argocd-cmd-params-cm` | `server.disable.auth` | `"false"` | Turns off authentication |
| `argocd-cmd-params-cm` | `applicationsetcontroller.enable.scm.providers` | `"false"` if not used | Disables SCM provider and PR generators |
| `argocd-cmd-params-cm` | `applicationsetcontroller.allowed.scm.providers` | exact SCM URLs | Stops generators from calling arbitrary SCM hosts |
| Repository Secret | label `argocd.argoproj.io/secret-type` | `repository` or `repo-creds` | Per-repo credential or URL-prefix template |
| Repository Secret | `project` | team project name | Only that project can use the credential |

Useful commands:

```bash
argocd admin settings rbac validate --policy-file policy.csv
argocd admin settings rbac can role:team-a get applications 'team-b/*' --policy-file policy.csv
argocd proj get team-a
argocd proj windows list prod
argocd app diff team-a-api
```

## Flux

| Controller | Flag | Secure value | Why |
|---|---|---|---|
| kustomize-controller | `--no-cross-namespace-refs` | `true` | A tenant cannot point at sources in other namespaces |
| kustomize-controller | `--default-service-account` | a low-privilege SA name | Objects without `serviceAccountName` fail closed |
| kustomize-controller | `--no-remote-bases` | `true` | Blocks Kustomize bases fetched from remote URLs |
| helm-controller | `--no-cross-namespace-refs` | `true` | Same for HelmRelease chart sources |
| helm-controller | `--default-service-account` | a low-privilege SA name | Same for HelmRelease |
| notification-controller | `--no-cross-namespace-refs` | `true` | Alerts cannot reference providers in other namespaces |

Set these as patches in `clusters/<name>/flux-system/kustomization.yaml` so `flux bootstrap` keeps them.

Source verification fields:

- `GitRepository.spec.verify.mode`: `HEAD`, `Tag` or `TagAndHEAD`, with `spec.verify.secretRef` to a Secret of armored OpenPGP public keys.
- `OCIRepository.spec.verify.provider`: `cosign` or `notation`, with `secretRef` for a public key, or `matchOIDCIdentity` (`issuer`, `subject` regexes) for keyless cosign.

Useful commands:

```bash
flux check
flux get sources all -A
flux diff kustomization team-a-apps --path ./deploy/prod
flux events -A --types=Warning
```

## SOPS

```yaml
# .sops.yaml
creation_rules:
  - path_regex: clusters/prod/.*\.yaml
    encrypted_regex: ^(data|stringData)$
    age: age1examplepublickeynotreal0000000000000000000000000000000
```

The decryption Secret for Flux holds the private key under a key ending in `.agekey`. Keep one age key per environment so a staging key cannot decrypt prod.
