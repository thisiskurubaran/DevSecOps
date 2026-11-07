---
name: artifact-signing
description: Set up and review signing and provenance for build artifacts and container images (Sigstore cosign keyless signing with OIDC in CI, SLSA build provenance with actions/attest-build-provenance or slsa-github-generator, SBOM attestations, npm provenance, PyPI trusted publishing) and enforce verification at deploy time with cosign verify, gh attestation verify, Kyverno verifyImages or Sigstore policy-controller. Use when the user wants to sign images or release files, add provenance or attestations to a release workflow, verify signatures before deploy, pin images by digest, or asks why a cosign or attestation check fails.
---

# Artifact Signing

Prove that an artifact came from your pipeline and was not swapped on the way to production. Signing alone does nothing: the value comes from a verifier that checks the signer identity and refuses anything else. Set up both ends, sign in CI and verify at deploy.

## When to use

- The user wants to sign container images or release binaries with cosign, or move from a long-lived cosign key to keyless signing.
- The user asks for SLSA provenance, build attestations, or SBOM attestations on a GitHub Actions or GitLab release.
- The user wants the cluster or deploy step to reject unsigned images (Kyverno `verifyImages`, Sigstore policy-controller, a `cosign verify` gate).
- A `cosign verify`, `gh attestation verify` or `slsa-verifier` command fails and the user wants to know why.
- The user publishes to npm or PyPI and wants provenance or token-free publishing.
- A deploy manifest references images by tag and should move to digests.

Not for: reviewing incoming dependencies, CVEs or the contents of an SBOM (use `dependency-supply-chain`), Dockerfile hardening and image scans (use `container-security`), auditing CI workflows for injection, token scope or unpinned actions in general (use `pipeline-hardening`), or writing admission policies unrelated to signatures (use `policy-as-code`).

## Steps

1. Map the artifacts. List what gets released (images, tarballs, binaries, npm or PyPI packages), where it is built (CI system, runner type), where it is stored (registry, release page) and where it is consumed (cluster, deploy script, end users).
2. Find the digest. Every signature and attestation must point at an immutable digest (`sha256:...`), never a tag. In GitHub Actions, `docker/build-push-action` exposes it as `steps.<id>.outputs.digest`. Elsewhere use `crane digest ghcr.io/example-org/app:1.4.0` or `docker buildx imagetools inspect`.
3. Pick the signing mode. Prefer keyless: CI gets an OIDC token, Fulcio issues a short-lived certificate bound to the workflow identity, and the signature is logged in Rekor. Use a KMS key (`cosign sign --key awskms://...`) only for air-gapped or private Sigstore setups. Flag any `cosign.key` file stored as a repo secret.
4. Set job permissions. Keyless signing and attestations need `id-token: write`. GitHub attestations also need `attestations: write`; pushing signatures to GHCR needs `packages: write`. Grant these on the release job only, not the whole workflow.
5. Add signing and provenance after the push step:
   - Images: `cosign sign --yes ghcr.io/example-org/app@${DIGEST}`.
   - Provenance: `actions/attest-build-provenance` with `subject-name` and `subject-digest` (add `push-to-registry: true` for images), or the `slsa-github-generator` reusable workflows for SLSA Build L3 isolation.
   - SBOM: generate with Syft or Trivy, then attach with `actions/attest-sbom` or `cosign attest --yes --type cyclonedx --predicate sbom.cdx.json IMAGE@DIGEST`.
   - Files: `cosign sign-blob --yes --bundle app.tar.gz.sigstore.json app.tar.gz`, and upload the bundle with the release.
6. Set up verification where the artifact is consumed. Pin the exact signer identity: the workflow file path and ref, plus the OIDC issuer. A check that accepts any identity, or `--certificate-identity-regexp '.*'`, proves nothing.
7. Pin consumers to digests. Deploy manifests, Helm values and `FROM` lines reference `image@sha256:...`. Kyverno `mutateDigest: true` can rewrite tags at admission, but the source should still pin.
8. Test both paths. Verify a signed image passes, then try an unsigned image or one signed by another workflow and confirm it is rejected. Run admission policies in audit mode first, check reports, then switch to enforce.
9. Write the output: findings table, fixed workflow snippet, and the verify command or policy.

## Checklist

Signing in CI:

- Signs by digest from the build step output, not by tag.
- Keyless with `id-token: write` scoped to the release job. No private key in repo secrets unless KMS backed.
- `sigstore/cosign-installer` and attestation actions pinned to a full commit SHA. Exception: `slsa-github-generator` must be referenced by version tag (`@v2.1.0`), its verifier checks the tag.
- Signing runs only on trusted triggers (push to main, tags, releases), never on `pull_request_target` or forks.
- Signs after push, in the same job that built the image, so the digest cannot be swapped between jobs.
- Release files have a Sigstore bundle or `.intoto.jsonl` provenance uploaded next to them.

Provenance and SBOM:

- Provenance subject digest matches the published artifact (`sha256sum app.tar.gz` or the image digest).
- Builder is a hosted runner. `gh attestation verify --deny-self-hosted-runners` passes, or the self-hosted risk is written down.
- SBOM is attested to the image digest, not just uploaded as a build artifact.
- Predicate type is explicit (`cyclonedx`, `spdxjson`, `slsaprovenance1`) so verifiers can filter on it.

Verification at deploy:

- `cosign verify` uses exact `--certificate-identity` and `--certificate-oidc-issuer`. Regexp flags are anchored (`^https://github\.com/example-org/`) and narrow.
- Identity includes the ref (`@refs/heads/main` or `@refs/tags/v*`) so a feature branch workflow cannot produce a deployable signature.
- Kyverno: `verifyImages` with `keyless.subject` and `keyless.issuer`, `required: true`, `verifyDigest: true`, `failureAction: Enforce` after an audit period. `imageReferences` covers every registry you ship from.
- policy-controller: a `ClusterImagePolicy` with `identities` (issuer and subject), and target namespaces labeled `policy.sigstore.dev/include=true`.
- System namespaces and third-party images have their own policy or a documented exclusion, not a blanket wildcard bypass.
- GitHub attestations verified with `gh attestation verify ... --repo` or `--owner`, plus `--signer-workflow` when a reusable workflow does the build.

Package registries:

- npm: `npm publish --provenance` from CI with `id-token: write`, or npm trusted publishing configured for the repo so no `NPM_TOKEN` is stored. Consumers can run `npm audit signatures`.
- PyPI: trusted publisher configured on PyPI, `pypa/gh-action-pypi-publish` with `id-token: write` in a protected `environment`, no `PYPI_API_TOKEN` secret. Attestations are on by default in current versions.
- Old long-lived publish tokens revoked once OIDC publishing works.

See [references/verify-policies.md](references/verify-policies.md) for full Kyverno, policy-controller, slsa-github-generator and verify command samples.

## Output format

Findings table, most severe first:

| Severity | File | Line | Issue | Fix |
|---|---|---|---|---|
| Critical | k8s/policy.yaml | 14 | `verifyImages` accepts any keyless subject | Set `subject` to the release workflow path and ref |
| High | .github/workflows/release.yml | 41 | `cosign sign ghcr.io/example-org/app:latest` signs a tag | Sign `@${{ steps.build.outputs.digest }}` |
| High | .github/workflows/release.yml | 8 | `id-token: write` at workflow level, runs on `pull_request` | Move to release job, trigger on tags only |
| Medium | deploy/values.yaml | 3 | Image pinned by tag | Pin `image@sha256:<digest>` |

Then:

1. The fixed workflow job or policy.
2. The exact verify command for the consumer, with real identity and issuer values filled in.
3. How to test: one command that should pass, one that should fail.

Severity: Critical (verification bypassable or missing on production deploy, signing key exposed), High (signs tags, overbroad identity, signing on untrusted triggers), Medium (tag-based deploys, missing SBOM or provenance, policy in audit only with no plan), Low (missing bundle upload, docs).

## Examples

Bad: long-lived key in a secret, signs a tag, verify step trusts anything signed with that key.

```yaml
on: [push, pull_request]
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - run: docker push ghcr.io/example-org/app:latest
      - run: cosign sign --key env://COSIGN_KEY ghcr.io/example-org/app:latest
        env:
          COSIGN_KEY: ${{ secrets.COSIGN_KEY }}
```

Good: keyless, by digest, scoped permissions, provenance pushed to the registry.

```yaml
on:
  push:
    tags: ["v*"]
permissions:
  contents: read
jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write
      attestations: write
    steps:
      - uses: actions/checkout@<full-sha> # v4
      - uses: sigstore/cosign-installer@<full-sha> # v3
      - uses: docker/login-action@<full-sha> # v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: build
        uses: docker/build-push-action@<full-sha> # v6
        with:
          push: true
          tags: ghcr.io/example-org/app:${{ github.ref_name }}
      - run: cosign sign --yes "ghcr.io/example-org/app@${DIGEST}"
        env:
          DIGEST: ${{ steps.build.outputs.digest }}
      - uses: actions/attest-build-provenance@<full-sha> # v2
        with:
          subject-name: ghcr.io/example-org/app
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true
```

Bad verify: proves only that someone, somewhere, signed it.

```bash
cosign verify --certificate-identity-regexp '.*' --certificate-oidc-issuer-regexp '.*' ghcr.io/example-org/app:latest
```

Good verify: exact workflow, ref, issuer and digest.

```bash
cosign verify \
  --certificate-identity "https://github.com/example-org/app/.github/workflows/release.yml@refs/tags/v1.4.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/example-org/app@sha256:<digest>

gh attestation verify oci://ghcr.io/example-org/app@sha256:<digest> --repo example-org/app
```
