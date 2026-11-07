---
name: crypto-review
description: Review how code and config use cryptography (weak hashes and ciphers, ECB or unauthenticated CBC, nonce reuse, hardcoded keys, non-CSPRNG tokens, password hashing parameters, non-constant-time MAC checks, RSA padding, key sizes, JWT algorithms, TLS versions and disabled certificate validation, home-rolled crypto) with Semgrep, CodeQL, testssl.sh and sslyze, and return a findings table with fixed code. Use when the user asks if their encryption, hashing, signing, random token generation or TLS setup is safe, shares code that imports crypto libraries, or opens a PR that touches encryption, key handling or TLS config.
---

# Crypto Review

Most crypto bugs are not broken math. They are a reused nonce, an `AES/ECB` default, a key in a constant, `Math.random()` for a reset token, or `verify=False` left in from debugging. Find where the code calls crypto primitives, check each call against the checklist, and replace low-level code with a high-level library where you can.

## When to use

- The user shares code that encrypts, decrypts, hashes, signs, verifies or generates tokens.
- A PR touches `crypto`, `cipher`, `hashlib`, `javax.crypto`, `crypto/tls`, `ssl`, or TLS settings in a client, server, proxy or load balancer config.
- The user asks "is this encryption safe", "which algorithm should I use", or "why does Semgrep flag MD5 here".
- Someone wants a crypto inventory, for example to find SHA-1, RSA-1024 or quantum-vulnerable algorithms.

Not for: login flows, sessions, OAuth and JWT validation logic (use `auth-review`), storing, scanning for and rotating secrets (use `secrets-management`), HSTS, CSP and other response headers (use `security-headers`), or a full OWASP Top 10 pass over an app (use `security-audit`).

## Steps

1. Inventory crypto use. Grep for the primitives, then read each call site:
   - `grep -rnE "md5|sha1|DES|RC4|ECB|createCipheriv|Cipher\.getInstance|AESGCM|Fernet|NewGCM|randomBytes|Math\.random|SecureRandom|math/rand|verify=False|rejectUnauthorized|InsecureSkipVerify|ssl\._create_unverified_context" src/`
   - List each hit as: purpose (password, integrity, confidentiality, token, signature), algorithm, mode, key source.
2. Run scanners to seed the review:
   - `semgrep --config p/security-audit --metrics=off .` (registry rules flag weak hashes, ECB, insecure random and disabled TLS checks across languages).
   - `bandit -r src -ll` (Python) and `gosec ./...` (Go) cover weak hashes, `random`, `math/rand` and skipped cert checks.
   - CodeQL with the `security-extended` suite for your language, which includes weak-crypto and disabled-certificate queries.
3. For each hash, decide if it is used for security. MD5 for a cache key or ETag is fine. MD5 or SHA-1 for signatures, integrity against tampering, or passwords is not. In Python 3.9+, mark the safe cases with `hashlib.md5(data, usedforsecurity=False)` so scanners and FIPS builds stop flagging them.
4. Check symmetric encryption: algorithm, mode, nonce source, and whether ciphertext is authenticated. Follow the key back to where it comes from.
5. Check randomness for every token, key, nonce, salt and ID that must be unguessable.
6. Check comparisons of MACs, signatures, API keys and reset tokens for constant-time compare.
7. Check asymmetric crypto: RSA padding, key sizes, curve choice, signature scheme.
8. Check TLS on both sides. Server: minimum version and cipher suites (run `testssl.sh https://app.example.com` or `sslyze app.example.com` against a test host). Client: certificate and hostname validation never turned off, including in test helpers that ship.
9. Flag home-rolled crypto: custom XOR schemes, hand-built encrypt-then-MAC, own padding, own KDF. Recommend a high-level library instead of fixing the construction.
10. Note quantum-vulnerable algorithms (RSA, ECDH, ECDSA) in an inventory list. Do not propose a rewrite, only where they are used and whether the library has a migration path.
11. Write fixes as code in the project's language and report with the output format.

## Checklist

Algorithms:

- No MD5 or SHA-1 for signatures, certificates, tamper-evident checksums, or passwords. Use SHA-256 or better. HMAC-SHA1 is not broken, but new code should use HMAC-SHA256.
- No DES, 3DES, RC4, Blowfish, or `AES/ECB`. In Java, `Cipher.getInstance("AES")` defaults to ECB with most providers: always give the full transformation.

Symmetric encryption:

- Authenticated encryption only: AES-GCM or ChaCha20-Poly1305. No AES-CBC or CTR without a MAC (padding oracle, bit flipping).
- Nonce is unique per key. A repeated nonce with the same key in GCM leaks the XOR of plaintexts and lets an attacker forge tags.
- 96-bit random GCM nonces are fine for a moderate message count per key (NIST caps random nonces at 2^32 messages per key). For high volume, rotate keys or use XChaCha20-Poly1305 with 192-bit random nonces.
- Nonce stored or sent with the ciphertext, not derived from a counter that resets on restart.
- Associated data used to bind context (record ID, tenant ID) where ciphertext could be swapped between rows.
- GCM tag checked before any plaintext is used. Do not truncate tags below 128 bits.

Key management:

- No keys in source, config files committed to git, or container images. Keys come from KMS or a secrets manager (hand off storage and rotation to `secrets-management`).
- Envelope encryption for data at rest: a KMS key encrypts per-object or per-tenant data keys, data keys encrypt data.
- Keys have a version ID stored with the ciphertext so rotation does not break decryption of old data.
- Separate keys per purpose. Do not reuse an encryption key as an HMAC key or a signing key.
- Keys derived from passwords use a KDF (argon2id, scrypt, PBKDF2), never a plain hash.

Randomness:

- Tokens, keys, nonces, salts and reset codes come from a CSPRNG: Python `secrets` or `os.urandom`, Node `crypto.randomBytes` or `crypto.randomUUID`, Java `SecureRandom`, Go `crypto/rand`.
- Never `Math.random()`, Python `random`, Java `java.util.Random`, Go `math/rand`, or a timestamp for anything security-related.
- Tokens have at least 128 bits of entropy.

Password hashing (storage only; login flow belongs to `auth-review`):

- argon2id (OWASP minimum: 19 MiB memory, 2 iterations, parallelism 1), bcrypt cost 10 or higher (12 is a common default), or scrypt (N=2^17, r=8, p=1).
- PBKDF2-HMAC-SHA256 only where FIPS requires it, with 600,000 or more iterations.
- bcrypt truncates input at 72 bytes. Do not pre-hash with raw SHA-256 bytes (NUL bytes truncate further).
- Parameters stored in the hash string so they can be raised later.

MACs and signatures:

- HMAC-SHA256 or better. HMAC keys at least 32 random bytes.
- Constant-time compare: `hmac.compare_digest` (Python), `crypto.timingSafeEqual` (Node, buffers must be equal length or it throws), `subtle.ConstantTimeCompare` (Go), `MessageDigest.isEqual` (Java). Never `==`, `equals`, or `strcmp` on secrets.
- Signatures: Ed25519, ECDSA P-256, or RSA-PSS. Verify before acting on the payload.

RSA and key sizes:

- RSA encryption uses OAEP (SHA-256). No PKCS#1 v1.5 encryption padding (Bleichenbacher). RSA signatures use PSS for new designs.
- RSA at least 2048 bits (3072 for keys that must last past 2030). ECC P-256 or Curve25519. AES-128 or AES-256.
- Prefer key agreement (X25519, ECDH) plus AEAD over encrypting data directly with RSA.

JWT at the crypto level:

- Reject `alg: none`. Pin the expected algorithm on verify so an RS256 public key cannot be used as an HS256 secret.
- HS256 secrets at least 32 random bytes, not a human password. Prefer ES256 or EdDSA when tokens cross service boundaries. Claim checks and session logic go to `auth-review`.

TLS:

- TLS 1.2 minimum, TLS 1.3 preferred. SSLv3, TLS 1.0 and 1.1 off.
- TLS 1.2 suites: ECDHE with AES-GCM or ChaCha20-Poly1305 only. No RSA key exchange, CBC-SHA1, 3DES, RC4, NULL or EXPORT suites.
- Certificate and hostname checks on: no `verify=False`, `ssl._create_unverified_context()`, `CERT_NONE`, `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`, `InsecureSkipVerify: true`, trust-all `X509TrustManager`, or `curl -k` in scripts. For internal CAs, pass the CA bundle instead.

Libraries:

- Prefer high-level APIs: libsodium (PyNaCl, libsodium-wrappers for JavaScript), Google Tink, Python `cryptography` `Fernet` or `AESGCM`, Go `crypto/cipher` AEAD or `golang.org/x/crypto/nacl/secretbox`.
- No custom ciphers, XOR "encryption", or hand-assembled encrypt-then-MAC.

Post-quantum readiness:

- Record where RSA, ECDH and ECDSA are used, key lifetimes, and which library and TLS stack each depends on. Data that must stay secret for years is the priority (harvest now, decrypt later). Note whether the stack supports ML-KEM hybrid key exchange (`X25519MLKEM768`) for TLS. Inventory only, no rewrite.

Safe APIs per language are in [references/safe-apis.md](references/safe-apis.md).

## Output format

Start with a two-line summary: scope reviewed and count by severity. Then one table, sorted by severity:

| # | Severity | File | Line | Purpose | Issue | Fix |
|---|---|---|---|---|---|---|
| 1 | Critical | `api/tls.go` | 18 | Outbound TLS | `InsecureSkipVerify: true` on the payments client | Remove it, load the internal CA into `RootCAs` |
| 2 | High | `app/crypto.py` | 42 | Field encryption | AES-CBC with no MAC, static IV | Switch to `AESGCM` with a random 12-byte nonce per message |
| 3 | Medium | `src/token.js` | 7 | Reset token | `Math.random()` token | `crypto.randomBytes(32).toString("base64url")` |

After the table:

1. Fixed code for each Critical and High.
2. Crypto inventory: algorithm, key size, purpose, location, quantum-vulnerable yes or no.
3. Scanner summary and any hits dropped as false positives with the reason (for example, "MD5 used as a cache key").
4. Open questions, such as where a key comes from at runtime.

Severity: Critical (TLS validation off on a live path, hardcoded production key, nonce reuse with GCM, unauthenticated decryption of attacker-controlled data), High (ECB or unauthenticated CBC, MD5 or SHA-1 passwords, predictable tokens, PKCS#1 v1.5 encryption, `alg: none` accepted), Medium (non-constant-time compare, weak password hash parameters, RSA-1024, TLS 1.0 enabled), Low (missing key version ID, no `usedforsecurity=False` on a non-security hash, inventory gaps).

## Examples

### Bad: static IV, CBC with no MAC, key in source (Python)

```python
from Crypto.Cipher import AES

KEY = b"0123456789abcdef"  # fake key, still hardcoded
IV = b"\x00" * 16

def encrypt(data: bytes) -> bytes:
    pad = 16 - len(data) % 16
    return AES.new(KEY, AES.MODE_CBC, IV).encrypt(data + bytes([pad]) * pad)
```

Same plaintext gives the same ciphertext, there is no integrity check, and anyone with the repo has the key.

### Good: AES-GCM via `cryptography`, random nonce, key from KMS

```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt(data_key: bytes, plaintext: bytes, record_id: str) -> bytes:
    # data_key is a 32-byte key decrypted from KMS (envelope encryption)
    nonce = os.urandom(12)
    return nonce + AESGCM(data_key).encrypt(nonce, plaintext, record_id.encode())

def decrypt(data_key: bytes, blob: bytes, record_id: str) -> bytes:
    return AESGCM(data_key).decrypt(blob[:12], blob[12:], record_id.encode())
```

`decrypt` raises `InvalidTag` if the ciphertext, nonce or record ID was changed.

### Bad: predictable token, timing leak, no cert check (Node.js)

```javascript
const token = Math.random().toString(36).slice(2);

if (req.headers["x-signature"] === expectedSig) { /* ... */ }

https.get("https://api.example.com", { rejectUnauthorized: false });
```

### Good

```javascript
const crypto = require("node:crypto");
const fs = require("node:fs");
const https = require("node:https");

const token = crypto.randomBytes(32).toString("base64url");

const got = Buffer.from(req.headers["x-signature"] ?? "", "hex");
const want = Buffer.from(expectedSig, "hex");
if (got.length === want.length && crypto.timingSafeEqual(got, want)) { /* ... */ }

https.get("https://api.example.com", { ca: fs.readFileSync("/etc/ssl/internal-ca.pem") });
```

### Good: TLS client config (Go)

```go
cfg := &tls.Config{
    MinVersion: tls.VersionTLS12,
    RootCAs:    pool, // internal CA loaded with x509.NewCertPool and AppendCertsFromPEM
}
client := &http.Client{Transport: &http.Transport{TLSClientConfig: cfg}}
```
