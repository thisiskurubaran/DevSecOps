# License policy and VEX

## License buckets

This is a common default. Your legal team's policy wins over this table.

| Bucket | Examples (SPDX IDs) | Typical rule |
|---|---|---|
| Permissive | MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC, 0BSD, Zlib | Allowed. Keep notices. |
| Weak copyleft | LGPL-2.1, LGPL-3.0, MPL-2.0, EPL-2.0 | Allowed with dynamic linking or unmodified use. Review if you modify the library. |
| Strong copyleft | GPL-2.0, GPL-3.0 | Review before use in anything you distribute (binaries, mobile apps, on-prem installs). |
| Network copyleft | AGPL-3.0, SSPL-1.0 | Usually blocked for SaaS code. Using it over the network can trigger source disclosure. |
| Non-commercial or source-available | BUSL-1.1, Elastic-2.0, CC-BY-NC-* | Review. Often blocked for commercial products. |
| No license / unknown | NOASSERTION, missing | Blocked until clarified. No license means no permission. |

Checks:

- Dual-licensed packages (`MIT OR GPL-3.0`): record which license you use.
- License changed between versions: compare the version you pin, not the latest.
- Vendored code copied into the repo still carries its license. Search for `LICENSE` files under `vendor/` or `third_party/`.

Tools:

- `trivy fs --scanners license --license-full .`
- `npx license-checker --production --summary` or `--failOn "AGPL-3.0;GPL-3.0"`
- `pip-licenses --format=markdown --with-urls`
- `go-licenses check ./... --disallowed_types=forbidden,restricted`
- `cargo deny check licenses` with a `deny.toml`

## VEX (Vulnerability Exploitability eXchange)

A VEX statement records whether a CVE in a component affects your product. It stops the same false alarm from coming back on every scan and tells customers why.

Statuses: `not_affected`, `affected`, `fixed`, `under_investigation`.

For `not_affected`, give a justification:

- `component_not_present`
- `vulnerable_code_not_present`
- `vulnerable_code_not_in_execute_path`
- `vulnerable_code_cannot_be_controlled_by_adversary`
- `inline_mitigations_already_exist`

OpenVEX example:

```json
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://example.com/vex/2026-0001",
  "author": "security@example.com",
  "timestamp": "2026-01-15T10:00:00Z",
  "version": 1,
  "statements": [
    {
      "vulnerability": { "name": "CVE-2099-0001" },
      "products": [{ "@id": "pkg:oci/invoice-api@sha256:0000000000000000000000000000000000000000000000000000000000000000" }],
      "status": "not_affected",
      "justification": "vulnerable_code_not_in_execute_path",
      "impact_statement": "The affected parser function is only used by the CLI tool, which is not shipped in this image."
    }
  ]
}
```

Use it:

- Trivy: `trivy image --vex vex.json <image>`
- Grype: `grype <image> --vex vex.json`
- Create with `vexctl create --product=... --vuln=CVE-... --status=not_affected --justification=...`

Review VEX statements on every major upgrade. A justification that was true for v1 may not hold for v2.
