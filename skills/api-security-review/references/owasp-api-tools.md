# OWASP API Top 10 (2023): tools and settings by category

A tool hit is a lead. BOLA, BFLA and business flow abuse need manual tests with two or more accounts, because no scanner knows whose data a response belongs to.

Spectral rule IDs below come from `@stoplight/spectral-owasp-ruleset` v2 (the 2023 edition). Names can change between releases: run `npx @stoplight/spectral-cli lint openapi.yaml -f json` and read the `code` field for the IDs your version uses.

## Spectral rules by category

| Category | Rule IDs (examples) | What it checks |
|---|---|---|
| API1 BOLA | `owasp:api1:2023-no-numeric-ids` | Path IDs are UUIDs or opaque strings, not sequential integers |
| API2 Auth | `owasp:api2:2023-no-http-basic`, `owasp:api2:2023-no-api-keys-in-url`, `owasp:api2:2023-write-restricted`, `owasp:api2:2023-jwt-best-practices` | No Basic auth or keys in URLs, write operations require security |
| API3 Properties | `owasp:api3:2023-no-additionalProperties`, `owasp:api3:2023-constrained-additionalProperties` | Request objects are closed or bounded |
| API4 Resources | `owasp:api4:2023-rate-limit`, `owasp:api4:2023-rate-limit-responses-429`, `owasp:api4:2023-array-limit`, `owasp:api4:2023-string-limit`, `owasp:api4:2023-integer-limit` | Rate limit headers, 429 response, `maxItems`, `maxLength`, `minimum`/`maximum` |
| API8 Config | `owasp:api8:2023-no-scheme-http`, `owasp:api8:2023-define-error-responses-401`, `owasp:api8:2023-define-error-responses-500`, `owasp:api8:2023-define-cors-origin` | HTTPS servers, error responses defined, CORS documented |
| API9 Inventory | `owasp:api9:2023-inventory-access`, `owasp:api9:2023-inventory-environment` | Servers declare audience and environment (`x-internal`, description) |

API5, API6, API7 and API10 have little or no spec-level coverage. Review them in code.

## 42Crunch-style spec audit

The 42Crunch audit scores a spec on security definitions and data validation. To do the same by hand, check:

- Global or per-operation `security` on every operation; `security: []` only on public routes with a comment saying why.
- Every `securityScheme` is used, and none is `http` with `scheme: basic` or `apiKey` with `in: query`.
- Strings: `maxLength` plus `pattern`, `format` or `enum`. Integers: `minimum`, `maximum`, `format: int32/int64`. Arrays: `maxItems`.
- Objects: `additionalProperties: false` on request bodies, `required` lists set.
- Each operation defines 400, 401, 403, 404, 429 and a default error response with a schema.
- Response schemas list only the fields the client needs.

In CI, the `42Crunch/api-security-audit-action` GitHub Action fails a build below a minimum score.

## Schemathesis

```bash
schemathesis run https://staging.example.com/openapi.json \
  --checks all \
  -H "Authorization: Bearer $TEST_TOKEN" \
  --max-examples 50 \
  --report junit
```

- `--checks all` includes server errors, response schema conformance, status code conformance, and acceptance of negative (invalid) data.
- Stateful testing follows OpenAPI links to chain create then read calls, which helps surface API1 when run with a second user's token.
- Point it at staging. It sends many writes.

## ZAP API scan

```bash
docker run --rm -v "$(pwd)":/zap/wrk:rw -t ghcr.io/zaproxy/zaproxy:stable \
  zap-api-scan.py -t https://staging.example.com/openapi.json -f openapi \
  -z "-config replacer.full_list(0).matchtype=REQ_HEADER \
      -config replacer.full_list(0).matchstr=Authorization \
      -config replacer.full_list(0).replacement='Bearer FAKE_TEST_TOKEN'" \
  -r zap.html -J zap.json
```

- `-f graphql` with `-t https://staging.example.com/graphql` for GraphQL.
- Use `-c rules.conf` to set rules to IGNORE, WARN or FAIL so the scan can gate CI.
- ZAP finds misconfiguration (API8), injection and SSRF candidates (API7). It does not find BOLA.

## GraphQL server settings

| Server | Depth / cost | Introspection off | Suggestions off |
|---|---|---|---|
| Apollo Server 4 | `validationRules: [depthLimit(8), createComplexityRule({ maximumComplexity: 1000 })]` | `introspection: process.env.NODE_ENV !== "production"` | Mask "Did you mean" in `formatError` or use a plugin |
| GraphQL Yoga / Envelop | `@escape.tech/graphql-armor` (max depth, cost, aliases, tokens) | `useDisableIntrospection()` | `blockFieldSuggestions` in graphql-armor |
| graphql-java | `MaxQueryDepthInstrumentation(8)`, `MaxQueryComplexityInstrumentation(1000)` | `NoIntrospectionGraphqlFieldVisibility` | Custom error handling |
| Strawberry (Python) | `QueryDepthLimiter(max_depth=8)`, `MaxAliasesLimiter`, `MaxTokensLimiter` | `DisableIntrospection` extension | `MaskErrors` |
| Hot Chocolate (.NET) | `.AddMaxExecutionDepthRule(8)`, cost analysis on by default in v14 | `.DisableIntrospection()` or `AllowIntrospection(false)` | `ModifyRequestOptions` |

Probe tools for a running GraphQL endpoint: `graphql-cop -t https://staging.example.com/graphql` (introspection, batching, field suggestions, GET-based CSRF) and InQL in Burp for schema extraction.
