# Standards map for auth-review

Section numbers below use OWASP ASVS 4.0.3. ASVS 5.0 regrouped this material into V6 (Authentication), V7 (Session Management), V8 (Authorization), V9 (Self-contained Tokens) and V10 (OAuth and OIDC). Cite whichever version the team audits against.

## OWASP ASVS 4.0.3

| Checklist group | ASVS section |
|---|---|
| Password rules, breached password checks | V2.1 Password Security |
| Rate limiting, lockout, MFA for admins | V2.2 General Authenticator Security |
| Password hashing (argon2id, bcrypt, PBKDF2) | V2.4 Credential Storage |
| Reset tokens, account recovery, enumeration | V2.5 Credential Recovery |
| SMS and email codes | V2.7 Out of Band Verifier |
| TOTP | V2.8 One Time Verifier |
| Session ID rotation on login | V3.2 Session Binding |
| Idle and absolute timeouts, logout, revoke other sessions | V3.3 Session Termination |
| Cookie flags, `__Host-` prefix | V3.4 Cookie-based Session Management |
| JWT and token-based sessions | V3.5 Token-based Session Management |
| Re-authentication before sensitive actions | V3.7 Defenses Against Session Management Exploits |
| Deny by default, central enforcement, least privilege | V4.1 General Access Control Design |
| Object-level checks, IDOR, CSRF on state changes | V4.2 Operation Level Access Control |
| Admin interfaces, step-up for admin | V4.3 Other Access Control Considerations |

## RFC 9700 (OAuth 2.0 Security Best Current Practice, January 2025)

| Checklist item | RFC 9700 section |
|---|---|
| Exact redirect URI matching, PKCE, `state`, `nonce`, mix-up defense | 2.1 Protecting Redirect-Based Flows |
| Authorization code with PKCE for all clients | 2.1.1 Authorization Code Grant |
| No implicit grant | 2.1.2 Implicit Grant |
| Sender-constrained access tokens (DPoP, mTLS) | 2.2.1 Access Tokens |
| Refresh token rotation or sender constraint for public clients | 2.2.2 Refresh Tokens |
| Audience-restricted, least-privilege access tokens | 2.3 Access Token Privilege Restriction |
| No resource owner password credentials grant | 2.4 Resource Owner Password Credentials Grant |
| Asymmetric client authentication (`private_key_jwt`, mTLS) | 2.5 Client Authentication |
| Attack background: redirect URI validation | 4.1 |
| Attack background: mix-up | 4.4 |
| Attack background: code injection | 4.5 |
| Attack background: CSRF | 4.7 |
| Attack background: PKCE downgrade | 4.8 |
| Attack background: refresh token protection | 4.14 |

## Related RFCs

- RFC 7636: PKCE.
- RFC 9207: `iss` parameter in the authorization response (mix-up defense).
- RFC 9449: DPoP, sender-constrained tokens.
- RFC 8705: mutual TLS client authentication and certificate-bound tokens.
- RFC 8725: JSON Web Token Best Current Practices (algorithm allowlist, `none`, key confusion).
