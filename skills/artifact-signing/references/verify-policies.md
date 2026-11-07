# Verification policies and commands

Samples for the consumer side of signing. Replace `example-org/app`, workflow paths and refs with your own. Check field names against the version you run: Kyverno and policy-controller both change their CRDs between releases.

## Kyverno verifyImages (keyless)

Kyverno 1.13 and later accept `failureAction` on the `verifyImages` entry. Older versions use `spec.validationFailureAction`. Start with `Audit`, read the policy reports, then switch to `Enforce`.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-release-signature
spec:
  webhookTimeoutSeconds: 30
  rules:
    - name: require-release-workflow-signature
      match:
        any:
          - resources:
              kinds: [Pod]
      verifyImages:
        - imageReferences:
            - "ghcr.io/example-org/*"
          failureAction: Audit
          required: true
          verifyDigest: true
          mutateDigest: true
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/example-org/app/.github/workflows/release.yml@refs/heads/main"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: https://rekor.sigstore.dev
```

To require an SBOM or provenance attestation as well, add an `attestations` block to the same `verifyImages` entry with `type: https://cyclonedx.org/bom` or `type: https://slsa.dev/provenance/v1` and the same attestor.

## Sigstore policy-controller

Policies apply only in namespaces labeled for it:

```bash
kubectl label namespace payments policy.sigstore.dev/include=true
```

```yaml
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: require-release-signature
spec:
  images:
    - glob: "ghcr.io/example-org/**"
  authorities:
    - keyless:
        url: https://fulcio.sigstore.dev
        identities:
          - issuer: https://token.actions.githubusercontent.com
            subject: https://github.com/example-org/app/.github/workflows/release.yml@refs/heads/main
```

Use `subjectRegExp` instead of `subject` only when several refs must pass, and anchor it.

## slsa-github-generator (SLSA Build L3)

Reference the reusable workflow by tag, not SHA. The generic generator takes base64 encoded `sha256sum` output from the build job.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      hashes: ${{ steps.hash.outputs.hashes }}
    steps:
      - run: make dist
      - id: hash
        run: echo "hashes=$(sha256sum dist/* | base64 -w0)" >> "$GITHUB_OUTPUT"
  provenance:
    needs: [build]
    permissions:
      actions: read
      id-token: write
      contents: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0
    with:
      base64-subjects: ${{ needs.build.outputs.hashes }}
      upload-assets: true
```

For images use `generator_container_slsa3.yml` with the `image` and `digest` inputs.

Verify:

```bash
slsa-verifier verify-artifact dist/app.tar.gz \
  --provenance-path app.intoto.jsonl \
  --source-uri github.com/example-org/app \
  --source-tag v1.4.0

slsa-verifier verify-image ghcr.io/example-org/app@sha256:<digest> \
  --source-uri github.com/example-org/app
```

## Command reference

```bash
# Image signature, exact identity
cosign verify \
  --certificate-identity "https://github.com/example-org/app/.github/workflows/release.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/example-org/app@sha256:<digest>

# SBOM attestation on an image
cosign verify-attestation --type cyclonedx \
  --certificate-identity "https://github.com/example-org/app/.github/workflows/release.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/example-org/app@sha256:<digest>

# Release file with a Sigstore bundle
cosign verify-blob app.tar.gz \
  --bundle app.tar.gz.sigstore.json \
  --certificate-identity "https://github.com/example-org/app/.github/workflows/release.yml@refs/tags/v1.4.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"

# GitHub artifact attestations
gh attestation verify app.tar.gz --repo example-org/app
gh attestation verify oci://ghcr.io/example-org/app@sha256:<digest> \
  --owner example-org \
  --signer-workflow example-org/build-templates/.github/workflows/build.yml \
  --deny-self-hosted-runners

# npm registry signatures and provenance for installed packages
npm audit signatures
```

## Common verify failures

| Error says | Usual cause |
|---|---|
| `none of the expected identities matched` | Identity string differs: wrong workflow file, branch vs tag ref, or a reusable workflow signed (its path is the identity) |
| `no signatures found` | Signed a different digest, or verifying a tag that moved after signing |
| `no matching attestations` (gh) | Wrong `--repo` or `--owner`, or attestation not pushed to the registry and checked with `oci://` |
| Kyverno timeout on admission | Registry or Rekor slow or blocked by egress rules; raise `webhookTimeoutSeconds` and allow egress |
