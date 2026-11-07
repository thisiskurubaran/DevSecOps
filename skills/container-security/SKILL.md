---
name: container-security
description: Harden Dockerfiles and container images (non-root user, pinned base digests, multi-stage builds, minimal or distroless bases, no secrets in layers) and turn Trivy or Grype image scan results into concrete base image and package fixes. Use when the user shares a Dockerfile, Containerfile or docker-compose file, asks to shrink or secure an image, or pastes an image scan report for a specific image.
---

# Container Security

Make images small, non-root, reproducible and free of secrets. When a scan report comes in, fix the cause (old base image, extra packages, build tools left in the runtime stage) instead of chasing CVEs one at a time.

## When to use

- The user shares a `Dockerfile`, `Containerfile`, or `docker-compose.yml` and asks for a review or hardening.
- The user wants a smaller image, a distroless or Alpine variant, or a multi-stage build.
- The user pastes `trivy image`, `grype`, or `docker scout cves` output for one image and asks how to fix it.
- A PR changes a Dockerfile or bumps a base image.

Not for: ranking findings across many scanners and repos (use `sast-dast-triage`), pod-level settings like `securityContext` and resource limits (use `k8s-manifest-review`), adding the scan step to CI (use `cicd-pipeline-builder`), or library CVEs in app code that need a dependency upgrade plan (use `dependency-supply-chain`).

## Steps

1. Read the Dockerfile top to bottom. Note the base image and tag, every `RUN` that installs packages, every `COPY`/`ADD`, `ARG`/`ENV` values, `USER`, `EXPOSE`, `ENTRYPOINT`/`CMD`, and `HEALTHCHECK`.
2. Run linters if available: `hadolint Dockerfile` and `checkov -f Dockerfile --framework dockerfile`. Use their rule IDs (DL3007, CKV_DOCKER_3) in findings.
3. Check the base image. Is it pinned by digest? Is it a current supported release? Could it be `gcr.io/distroless/*`, `cgr.dev/chainguard/*`, `*-slim`, or `alpine` instead of a full OS image?
4. Check the build shape. Compilers, package managers, test files and `.git` should stay in a builder stage. The final stage copies only the binary or app bundle.
5. Look for secrets. `ARG`/`ENV` holding tokens, `COPY .env`, `COPY ~/.npmrc`, `.git` copied in, private keys. Removing a file in a later layer does not remove it from the image. Use `RUN --mount=type=secret` instead.
6. Check runtime identity. A `USER` with a numeric UID (`USER 10001`) in the final stage. Files the app writes go to a dedicated directory owned by that user. No `chmod 777`.
7. If a scan report is provided, group findings by source: base OS packages, language packages, or binaries. For each group pick one fix: bump or swap the base, drop the package, or upgrade the library. Prefer the fix that clears the most criticals.
8. Rebuild and rescan: `docker build -t app:test .` then `trivy image --severity HIGH,CRITICAL --ignore-unfixed app:test`. Compare counts and image size (`docker image ls app:test`) before and after.
9. Write the output: findings table, the hardened Dockerfile, and the before/after numbers.

## Checklist

Base image:

- Pinned by digest: `FROM python:3.12-slim@sha256:<digest>`. A tag alone (`:latest`, `:3`) is not reproducible (hadolint DL3007).
- Supported release, not EOL (no `debian:buster`, `node:16`, `python:3.8`).
- Smallest base that runs the app. Static Go or Rust binaries can use `gcr.io/distroless/static-debian12:nonroot` or `scratch`.

Build:

- Multi-stage. Build tools (`gcc`, `build-essential`, `git`, `curl`) absent from the final stage.
- `.dockerignore` excludes `.git`, `.env*`, `node_modules`, `*.pem`, `tests/`, local config.
- `COPY` instead of `ADD` unless extracting a local tar (hadolint DL3020). No `ADD https://...` without checksum.
- Package installs pinned and cleaned in the same layer: `apt-get install -y --no-install-recommends pkg=1.2.3 && rm -rf /var/lib/apt/lists/*` (DL3008, DL3009, DL3015).
- `apk add --no-cache` on Alpine (DL3018, DL3019).
- Lockfile installs: `npm ci --omit=dev`, `pip install --no-cache-dir -r requirements.txt`.
- Build secrets through `RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci`, never `ARG NPM_TOKEN`.

Runtime:

- `USER` set to a non-zero UID in the final stage (CKV_DOCKER_3, DL3002).
- No `sudo` installed. No setuid binaries you do not need (`find / -perm -4000` in a debug build).
- `HEALTHCHECK` defined, or health handled by the orchestrator (CKV_DOCKER_2).
- Exec form for `ENTRYPOINT`/`CMD` so signals reach the process: `ENTRYPOINT ["/app/server"]`.
- Only needed ports in `EXPOSE`. No SSH daemon.
- Works with a read-only root filesystem: writes go to a mounted volume or `/tmp`.

Compose (if present):

- No `privileged: true`, no `network_mode: host`, no `/var/run/docker.sock` mount unless the service truly manages Docker.
- `cap_drop: [ALL]` and `security_opt: ["no-new-privileges:true"]`.
- Secrets through `secrets:` or an env file outside the repo, not inline `environment:` values.

Scan results:

- Use `--ignore-unfixed` to focus on actionable CVEs first, then review unfixed criticals for exposure.
- Record accepted CVEs in `.trivyignore` with a comment, an owner and an expiry date.
- Check the image for secrets too: `trivy image --scanners secret app:test`.

## Output format

Findings table, most severe first:

| Severity | File | Line | Issue | Fix |
|---|---|---|---|---|
| High | Dockerfile | 1 | `FROM node:latest` is unpinned and ships 300+ OS packages | `FROM node:20-bookworm-slim@sha256:<digest>` for build, distroless for runtime |
| High | Dockerfile | 9 | `ARG NPM_TOKEN` is stored in image history | `RUN --mount=type=secret,id=npmrc` |
| Medium | Dockerfile | - | No `USER`, container runs as root | Add `USER 10001` in final stage |

Then:

1. The full hardened Dockerfile.
2. Scan delta when a report was given: `Critical 12 -> 0, High 48 -> 3, size 1.1 GB -> 180 MB`.
3. Remaining accepted CVEs with reason and expiry.

Severity: Critical (secret in image, known exploited CVE reachable from the network), High (root user, unpinned or EOL base, fixable critical CVE), Medium (missing healthcheck, extra packages, fixable high CVE), Low (layer hygiene, labels).

## Examples

Bad: unpinned full base, secret in build arg, build tools and root at runtime.

```dockerfile
FROM node:latest
ARG NPM_TOKEN
WORKDIR /app
COPY . .
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc && npm install
EXPOSE 3000
CMD npm start
```

Good: pinned digest, multi-stage, build secret mount, distroless non-root runtime.

```dockerfile
# syntax=docker/dockerfile:1.7
FROM node:20-bookworm-slim@sha256:<digest> AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci --omit=dev
COPY src/ ./src/

FROM gcr.io/distroless/nodejs20-debian12:nonroot@sha256:<digest>
WORKDIR /app
COPY --from=build --chown=65532:65532 /app /app
USER 65532
EXPOSE 3000
ENTRYPOINT ["/nodejs/bin/node", "src/server.js"]
```

Build it with `docker build --secret id=npmrc,src=$HOME/.npmrc -t app:test .` so the token never lands in a layer.

Bad `.dockerignore` (missing). Good:

```text
.git
.env*
*.pem
node_modules
tests/
Dockerfile
```
