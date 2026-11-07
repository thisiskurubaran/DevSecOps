---
name: api-security-review
description: Review OpenAPI specs, GraphQL schemas and API endpoint code against the OWASP API Security Top 10 (2023), covering BOLA, broken auth, mass assignment and data exposure, rate limits and pagination caps, BFLA, SSRF, misconfiguration and API inventory, using Spectral with the OWASP ruleset, a 42Crunch-style spec audit, ZAP API scan and Schemathesis. Use when the user shares an openapi.yaml, swagger.json or GraphQL schema, asks for an API security review, or opens a PR that adds or changes API routes, resolvers or the spec.
---

# API Security Review

APIs fail in ways a general code audit tends to miss: one user reading another user's order by changing an ID, a `PATCH` that accepts `role: "admin"`, a list endpoint with no page size cap, a GraphQL query nested 40 levels deep. Lint the spec, read the handlers, then test the running API. The spec says what the API promises; the code and the live responses say what it does.

## When to use

- The user shares `openapi.yaml`, `openapi.json`, `swagger.json`, a `.graphql` schema, or a Postman collection and asks if it is secure.
- A PR adds or changes routes, controllers, resolvers, serializers, DTOs or the API spec.
- The user asks about BOLA/IDOR, mass assignment, rate limiting, GraphQL introspection or depth limits.
- Someone wants Spectral, 42Crunch, ZAP API scan or Schemathesis findings explained and fixed.

Not for: general OWASP Top 10 review of application code such as injection, XSS or session handling (use `security-audit`), creating new endpoints, validation and docs (use `api-scaffolder`), or design-stage analysis of a feature with no spec or code yet (use `threat-modeling`).

## Steps

1. Build the inventory. List every operation: method, path, auth scheme, roles allowed, and whether it takes an object ID. Compare the spec to the router (`grep -rnE "@(Get|Post|Put|Patch|Delete)Mapping|router\.(get|post|put|patch|delete)|@app\.(get|post|put|patch|delete)" src/`). Routes in code but not in the spec are shadow endpoints; routes in the spec marked deprecated but still served are zombie endpoints (API9).
2. Lint the spec with the OWASP ruleset:
   - `.spectral.yaml`: `extends: ["spectral:oas", "@stoplight/spectral-owasp-ruleset"]`
   - `npx @stoplight/spectral-cli lint openapi.yaml --fail-severity=warn`
3. Run a spec audit in the 42Crunch style, either with the 42Crunch tool (VS Code extension or `42Crunch/api-security-audit-action` in CI) or by hand: every operation has a `security` requirement or an explicit `security: []` with a reason; every string has `maxLength` and a `pattern` or `format`; every integer has `minimum` and `maximum`; every array has `maxItems`; objects set `additionalProperties: false`; responses are defined for 401, 403, 404, 429 and 4XX/5XX with a schema.
4. Read the handlers for each operation against the checklist. Spend the most time on operations that take an ID, write data, or are admin only. For each, answer: who is the caller, which object is touched, and where does the code check that this caller may touch it?
5. For GraphQL, review the server config and resolvers: depth limit, complexity or cost limit, alias and batch limits, introspection off in production, field suggestions off, and per-field authorization in resolvers (not only at the gateway).
6. Test the running API against a staging host, never production:
   - `schemathesis run https://staging.example.com/openapi.json --checks all -H "Authorization: Bearer $TEST_TOKEN"` finds 5xx errors, schema violations and accepted bad input.
   - `docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-api-scan.py -t https://staging.example.com/openapi.json -f openapi -r zap.html` (use `-f graphql` with the GraphQL endpoint).
   - BOLA and BFLA by hand: log in as user A and user B (and a non-admin), replay each request with the other user's token and IDs. Scanners cannot tell whose data a response belongs to.
7. Confirm each finding with the request that shows it (method, path, token used, body, response code). If you cannot reproduce it, mark it "needs verification".
8. Write fixes in two places when both apply: the spec change and the handler change. Rank and report using the output format.

## Checklist

API1 Broken object level authorization (BOLA)

- Every lookup by ID is scoped to the caller or tenant: `where(id: id, account_id: current_account.id)`, not `find(id)` followed by nothing.
- IDs in paths, query strings, bodies and headers all count. Nested routes (`/users/{userId}/orders/{orderId}`) check both levels.
- Random UUIDs reduce guessing but are not an access check.

API2 Broken authentication

- No HTTP Basic or API keys in query strings (`in: query`) for user data. Bearer tokens over HTTPS only.
- JWTs: signature verified, `alg` pinned (no `none`, no HS/RS confusion), `exp`, `iss` and `aud` checked, short lifetime with refresh rotation.
- Login, token, password reset and OTP endpoints are rate limited and lock out or slow down after failures.

API3 Broken object property level authorization

- Mass assignment: request bodies bind to an explicit DTO or allowlist. Fields such as `role`, `isAdmin`, `balance`, `ownerId`, `verified` are never writable by the client.
- Excessive data exposure: responses use a serializer or response schema, not `res.json(user)` on the ORM object. No `passwordHash`, internal flags, other users' emails.
- Spec has `additionalProperties: false` on request schemas and `readOnly: true` on server-set fields.

API4 Unrestricted resource consumption

- Rate limits per user and per IP, with `429` and `Retry-After` documented in the spec.
- List endpoints cap `limit`/`pageSize` (`maximum: 100`) and enforce it in code, not only in the spec.
- Upload size, request body size, string lengths, array lengths and timeouts are bounded.
- Costly operations (SMS, email, PDF export, AI calls) have per-account quotas.

API5 Broken function level authorization (BFLA)

- Admin and internal operations check role or permission in the handler or policy layer, not by hiding the route.
- Changing the method (`GET` to `DELETE`, `PUT` to `PATCH`) on a user route does not reach an admin action.

API6 Unrestricted access to sensitive business flows

- Flows that can be abused at scale (checkout, sign-up, coupon redeem, booking, referral) have bot controls: per-account limits, device or CAPTCHA checks, velocity rules.

API7 Server side request forgery

- Any field that takes a URL (webhooks, avatar import, PDF from URL) is checked against an allowlist, resolved IP is not private, link-local (`169.254.169.254`) or loopback, and redirects are not followed blindly.

API8 Security misconfiguration

- CORS does not reflect arbitrary `Origin` with `Access-Control-Allow-Credentials: true`.
- Errors return a generic body, no stack traces or SQL. Debug, actuator and metrics endpoints are not public.
- Spec `servers` use `https://` only. Security headers set (`Cache-Control: no-store` on sensitive responses).

API9 Improper inventory management

- Spec matches deployed routes. Old versions (`/v1`) are retired or held to the same auth and limits as current ones.
- Non-production hosts are not public and do not hold production data.

API10 Unsafe consumption of APIs

- Responses from third-party APIs are validated against a schema before use, with timeouts, TLS verification on and no blind redirect following.
- Data from partners is treated as untrusted input (no passing it into SQL, shell or HTML unescaped).

GraphQL

- Depth limit (`graphql-depth-limit`, typical max 7 to 10) and cost limit (`graphql-query-complexity` or the server's built-in cost analysis).
- Alias and batch limits so one request cannot run the login mutation 1000 times.
- `introspection: false` and field suggestions off in production; persisted queries for public clients where possible.
- Authorization in each resolver or a directive (`@auth`), including nested fields that reach other users' objects.

See [references/owasp-api-tools.md](references/owasp-api-tools.md) for Spectral rule IDs, ZAP and Schemathesis options, and GraphQL server settings mapped to each category.

## Output format

| Severity | OWASP | Operation | File | Line | Issue | Fix |
|---|---|---|---|---|---|---|
| Critical | API1 | GET /orders/{id} | src/orders/controller.ts | 42 | Order loaded by ID with no owner check; user B can read user A's orders | Query with `{ id, customerId: req.user.id }`, return 404 on miss |
| High | API3 | PATCH /users/me | src/users/controller.ts | 77 | Body spread into `User.update`, client can set `role` | Bind to `UpdateProfileDto` with allowlisted fields; spec `additionalProperties: false` |
| Medium | API4 | GET /products | openapi.yaml | 118 | `limit` has no `maximum`; code passes it straight to the query | Add `maximum: 100` in spec, clamp in code |

After the table:

1. Fixed code and spec snippets for each Critical and High.
2. Reproduction for each confirmed finding: request, token used, response.
3. Tool summary: Spectral, spec audit, Schemathesis and ZAP results with counts, and which findings you dropped as false positives with the reason.
4. Inventory gaps: shadow or zombie endpoints, operations with no auth defined.

Severity: Critical (read or change another user's or tenant's data, auth bypass, admin action as a normal user), High (mass assignment of privileged fields, sensitive data in responses, SSRF to internal hosts, no rate limit on login), Medium (missing pagination caps, permissive CORS without credentials, introspection on in production), Low (missing error schemas, loose string formats, spec hygiene).

## Examples

Bad: no owner check, body bound straight to the model, full object returned.

```ts
router.get("/orders/:id", auth, async (req, res) => {
  const order = await Order.findByPk(req.params.id);
  res.json(order);
});

router.patch("/users/me", auth, async (req, res) => {
  await User.update(req.body, { where: { id: req.user.id } });
  res.json(await User.findByPk(req.user.id));
});
```

Good: scoped query, allowlisted fields, explicit response shape.

```ts
router.get("/orders/:id", auth, async (req, res) => {
  const order = await Order.findOne({
    where: { id: req.params.id, customerId: req.user.id },
  });
  if (!order) return res.sendStatus(404);
  res.json(toOrderResponse(order));
});

router.patch("/users/me", auth, async (req, res) => {
  const { displayName, timezone } = UpdateProfile.parse(req.body); // zod, .strict()
  await User.update({ displayName, timezone }, { where: { id: req.user.id } });
  res.json(toProfileResponse(await User.findByPk(req.user.id)));
});
```

Bad spec: unbounded page size, open request schema.

```yaml
parameters:
  - name: limit
    in: query
    schema: { type: integer }
UpdateProfile:
  type: object
  properties:
    displayName: { type: string }
```

Good spec: bounded, closed, server fields read-only.

```yaml
parameters:
  - name: limit
    in: query
    schema: { type: integer, minimum: 1, maximum: 100, default: 20 }
UpdateProfile:
  type: object
  additionalProperties: false
  properties:
    displayName: { type: string, maxLength: 64, pattern: "^[A-Za-z0-9 ._-]+$" }
    role: { type: string, readOnly: true }
```
