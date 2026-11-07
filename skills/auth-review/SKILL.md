---
name: auth-review
description: Deep review of authentication and authorization code and config (OAuth 2.0 and OIDC flows with PKCE, state and nonce, JWT validation and JWKS rotation, refresh token rotation, session cookies and timeouts, password hashing, MFA and step-up, account recovery and enumeration, rate limiting and lockout, RBAC/ABAC/ReBAC policy checks and tenant isolation) against OWASP ASVS V2/V3/V4 and RFC 9700, returning a findings table with code fixes. Use when the user shares login, token, session, OAuth/OIDC client or authorization server config, middleware or policy code, asks if their JWT or session handling is safe, or opens a PR that changes auth or permission logic.
---

# Auth Review

Most auth bugs are one missing check: a JWT decoded but never verified, a `redirect_uri` matched by prefix, a session ID that survives login, a policy check in the controller that one route forgot. Trace each credential from where it is issued to where it is checked, and each permission decision from the request to the data it guards.

## When to use

- The user shares login, logout, sign-up, password reset, MFA, OAuth callback or token refresh code.
- The user shares OAuth/OIDC client settings, identity provider config (Keycloak, Auth0, Okta, Cognito, Entra ID), JWT middleware, or session and cookie config.
- The user asks "is this JWT validation safe", "should I use implicit flow", "how long should sessions last", or "is bcrypt cost 8 enough".
- A PR touches auth middleware, guards, decorators, policy files (Casbin, OPA, Cedar, OpenFGA), role tables or tenant scoping.

Not for: a general OWASP Top 10 audit of the codebase (use `security-audit`), endpoint-by-endpoint API review including BOLA at the API layer (use `api-security-review`), cloud IAM policies and roles in AWS, GCP or Azure (use `cloud-iam-review`), or design-stage analysis of a feature with no code yet (use `threat-modeling`).

## Steps

1. Map the auth surface. List every way a caller proves identity (password, OAuth/OIDC, API key, magic link, passkey), where tokens or sessions are issued, where they are checked, and where they are revoked. Find entry points with `grep -rniE "jwt|jwks|session|oauth|oidc|login|logout|refresh|password|mfa|otp|authorize|permission|role|tenant" src/`.
2. Read the identity provider and client config before the code. Allowed grant types, registered redirect URIs, token lifetimes, refresh token rotation, PKCE requirement, signing algorithms.
3. Walk each OAuth/OIDC flow from the first redirect to the callback. Check that `state`, `nonce` and `code_verifier` are generated per request, stored server side or in a signed cookie, and compared on return.
4. Find every place a token is accepted. For each, confirm signature verification with a pinned algorithm list and claim checks. Look for `decode` calls that skip verification.
5. Review session handling: cookie flags, ID rotation on login and privilege change, idle and absolute timeouts, logout that kills the server-side session.
6. Review credential storage and recovery: hashing algorithm and parameters, reset token entropy and expiry, responses that leak whether an account exists, rate limits on every credential endpoint.
7. Review authorization. Find where the decision is made. One central policy function or middleware is good; checks scattered across handlers usually means one is missing. Confirm deny by default, object-level checks, and tenant scoping on every query.
8. Test what you can on a staging host: replay a token with `alg` changed, a session cookie after logout, a reset link twice, user A's object ID with user B's session. `jwt_tool` helps with the token tests.
9. Mark findings you cannot reproduce or trace as "needs verification". Rank and report using the output format, with fixed code for each Critical and High.

## Checklist

OAuth 2.0 and OIDC (RFC 9700)

- Authorization code flow with PKCE (`code_challenge_method=S256`) for every client, public and confidential. No implicit flow (`response_type=token` or `id_token token`), no resource owner password grant.
- `redirect_uri` compared by exact string match on the authorization server. No wildcards, no prefix or substring matching. Native apps may vary only the loopback port.
- `state` is random per request and checked on callback (or PKCE covers CSRF and the server enforces it). OIDC `nonce` is sent and checked against the ID token.
- With more than one authorization server, defend against mix-up: check the `iss` response parameter (RFC 9207) or use a distinct redirect URI per issuer.
- ID token checked fully: signature, `iss`, `aud` contains your `client_id`, `exp`, `nonce`. The access token is not used as proof of login in the client.
- Client secrets are not shipped in mobile or SPA bundles. Prefer `private_key_jwt` or mTLS client auth for confidential clients.
- No open redirects after login: post-login `returnTo` values are checked against an allowlist of relative paths.

JWT validation

- Signature always verified. Algorithm comes from a server-side allowlist, never from the token header. `none` rejected. No HS256 accepted where RS256 or ES256 is expected (key confusion).
- `iss`, `aud`, `exp` checked and required; `nbf` honored. Small clock skew only (`leeway` of 30 to 60 seconds).
- Keys fetched from the issuer's JWKS endpoint, selected by `kid`, cached with refresh on unknown `kid`. `jku` and `x5u` headers from the token are ignored.
- Access tokens short lived (5 to 15 minutes). No sensitive data in the payload: it is encoded, not encrypted.
- Refresh tokens rotate on every use, and reuse of an old refresh token revokes the whole token family. Public clients get rotated or sender-constrained (DPoP, RFC 9449) refresh tokens.
- A revocation path exists for logout and compromise: short access token lifetime plus refresh token revocation, or a denylist by `jti`.

Sessions (ASVS V3)

- Session cookie: `HttpOnly`, `Secure`, `SameSite=Lax` or `Strict`, `Path=/`, no `Domain` unless needed. The `__Host-` prefix where possible.
- Session ID regenerated on login, logout, and privilege change (MFA completed, role change). Prevents fixation.
- Idle timeout and absolute timeout both enforced server side. Rough guide: 15 to 30 minutes idle for sensitive apps, 8 to 24 hours absolute.
- Logout destroys the server-side session, not only the cookie. Password change and "sign out everywhere" revoke other sessions and refresh tokens.
- State-changing requests with cookie auth have CSRF protection beyond `SameSite` (token or origin check).

Passwords and credentials (ASVS V2)

- Hash with argon2id (OWASP minimum: 19 MiB memory, 2 iterations, parallelism 1) or bcrypt with cost 10 or higher. scrypt or PBKDF2-HMAC-SHA256 (600,000 iterations) when FIPS is required. Never MD5, SHA-1, SHA-256 alone, or reversible encryption.
- bcrypt truncates input at 72 bytes; reject or pre-handle longer passwords rather than silently cutting them.
- Rehash on login when parameters are below current settings.
- Minimum length 8 (12 or more without MFA), maximum at least 64, no composition rules, check against breached password lists.
- Comparisons of tokens and hashes use constant-time functions (`hmac.compare_digest`, `crypto.timingSafeEqual`).

MFA, recovery and enumeration

- MFA offered for all users and required for admins. TOTP or WebAuthn preferred over SMS. Step-up (fresh MFA or re-auth) before changing email, password, MFA settings, payout details, or viewing secrets.
- MFA cannot be skipped by calling the post-MFA endpoint directly; the session carries an "MFA pending" state until verified.
- Reset tokens: at least 128 bits from a CSPRNG, stored hashed, single use, expire in 15 to 60 minutes, invalidated when a new one is issued or the password changes.
- Login, sign-up and reset return the same message and similar timing whether or not the account exists.
- Recovery does not bypass MFA unless the user proves a second factor or uses recovery codes.

Rate limiting and lockout

- Per-account and per-IP limits on login, MFA verify, reset request, reset confirm, and token endpoints.
- Lockout is temporary with backoff, not permanent (permanent lockout is a denial of service on any known username).
- Failed attempts and lockouts are logged without the password or token value.

Authorization (ASVS V4)

- Deny by default: a route with no explicit policy is rejected, not allowed. Check this in the router or framework config.
- One central policy check (middleware, guard, policy engine) called for every protected route. Grep for routes that skip it.
- Object-level checks on every read and write: the query is scoped to the caller (`WHERE id = ? AND owner_id = ?`), or the policy is evaluated on the loaded object.
- Tenant isolation: `tenant_id` comes from the authenticated session or token, never from the request body, query or a header the client controls. Every query filters by it; row-level security or a scoped repository enforces it.
- RBAC: roles and permissions checked server side, not inferred from UI state. ABAC/ReBAC (OPA, Cedar, OpenFGA, SpiceDB): policies have tests, and the app fails closed when the policy engine is down.
- Users cannot grant themselves roles or change their own `role`, `tenant_id` or `is_admin` fields.

See [references/standards-map.md](references/standards-map.md) for the ASVS 4.0.3 and RFC 9700 sections behind each checklist group.

## Output format

| Severity | Area | Standard | File | Line | Issue | Fix |
|---|---|---|---|---|---|---|
| Critical | JWT | ASVS V3.5 | src/auth/middleware.ts | 18 | `jwt.decode` used, signature never checked; any forged token is accepted | `jwtVerify` with JWKS, `algorithms: ["RS256"]`, `issuer`, `audience` |
| High | Session | ASVS V3.2 | app/views/login.py | 44 | Session ID not rotated on login (fixation) | Call `request.session.cycle_key()` or use `django.contrib.auth.login` |
| Medium | Recovery | ASVS V2.5 | src/reset.ts | 61 | "No account with that email" leaks account existence | Same response for both cases, send mail only if the account exists |

After the table:

1. Fixed code for each Critical and High.
2. Flow diagram or step list for each OAuth/OIDC flow reviewed, with where each check happens.
3. Config changes for the identity provider (grant types, redirect URIs, lifetimes, rotation).
4. Open questions: anything that depends on infra you could not see, such as a gateway that might validate tokens upstream.

Severity: Critical (auth bypass, forged tokens accepted, cross-tenant access, any user can act as admin), High (session fixation, no refresh token rotation for public clients, weak password hashing, missing object-level check, no rate limit on login or MFA), Medium (account enumeration, long-lived access tokens, missing absolute timeout, no step-up on sensitive changes), Low (missing `__Host-` prefix, verbose auth errors, hygiene).

## Examples

Bad: token decoded without verification, algorithm taken from the header, no claim checks.

```js
const jwt = require("jsonwebtoken");

function auth(req, res, next) {
  const token = req.headers.authorization?.split(" ")[1];
  req.user = jwt.decode(token); // no signature check
  next();
}
```

Good: JWKS with `kid` lookup, pinned algorithm, issuer and audience required (`jose`).

```js
import { createRemoteJWKSet, jwtVerify } from "jose";

const JWKS = createRemoteJWKSet(new URL("https://id.example.com/.well-known/jwks.json"));

async function auth(req, res, next) {
  try {
    const token = req.headers.authorization?.replace(/^Bearer /, "");
    const { payload } = await jwtVerify(token, JWKS, {
      issuer: "https://id.example.com/",
      audience: "orders-api",
      algorithms: ["RS256"],
    });
    req.user = payload;
    next();
  } catch {
    res.sendStatus(401);
  }
}
```

Bad: weak hash, session kept across login, tenant taken from the request.

```python
user = User.objects.get(email=email)
if user.password == hashlib.sha256(password.encode()).hexdigest():
    request.session["user_id"] = user.id
invoices = Invoice.objects.filter(tenant_id=request.GET["tenant"])
```

Good: argon2id with rehash, session rotated, tenant from the authenticated user.

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()  # argon2id, defaults meet OWASP minimums

try:
    ph.verify(user.password_hash, password)
except VerifyMismatchError:
    return deny()
if ph.check_needs_rehash(user.password_hash):
    user.password_hash = ph.hash(password)
    user.save(update_fields=["password_hash"])
request.session.cycle_key()
request.session["user_id"] = user.id
invoices = Invoice.objects.filter(tenant_id=request.user.tenant_id)
```

Bad cookie config (Express):

```js
app.use(session({ secret: process.env.SESSION_SECRET, cookie: {} }));
```

Good:

```js
app.use(session({
  name: "__Host-sid",
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  rolling: true, // idle timeout via maxAge; enforce absolute timeout in middleware
  cookie: { httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 30 * 60 * 1000 },
}));
// on login: req.session.regenerate(...) before setting req.session.userId
```
