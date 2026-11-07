# Safe crypto APIs by language

Use these as the replacement column when writing fixes. A grep hit in the "Avoid" column is a lead: check what the call is used for before reporting it.

## Python

| Need | Avoid | Use |
|---|---|---|
| Symmetric encryption | `AES.MODE_ECB`, `AES.MODE_CBC` without HMAC, custom XOR | `cryptography` `AESGCM`, `ChaCha20Poly1305`, or `Fernet`; PyNaCl `nacl.secret.SecretBox` |
| Random tokens | `random.random`, `random.choice`, `uuid.uuid1` | `secrets.token_urlsafe(32)`, `secrets.token_bytes`, `os.urandom` |
| Password hashing | `hashlib.sha256(pw)`, `md5` | `argon2-cffi` `PasswordHasher` (argon2id), `bcrypt.hashpw` with `bcrypt.gensalt()` |
| MAC check | `sig == expected` | `hmac.compare_digest(sig, expected)` |
| RSA encryption | `padding.PKCS1v15()` for encrypt | `padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)` |
| RSA signatures | PKCS1v15 in new designs | `padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)`, or `Ed25519PrivateKey` |
| TLS client | `verify=False`, `ssl._create_unverified_context()`, `CERT_NONE` | `requests.get(url, verify="/path/ca.pem")`, `ssl.create_default_context(cafile=...)` |
| Non-security hash | `hashlib.md5(data)` flagged by scanners | `hashlib.md5(data, usedforsecurity=False)` (3.9+) |

## JavaScript and TypeScript (Node.js)

| Need | Avoid | Use |
|---|---|---|
| Symmetric encryption | `aes-*-ecb`, `aes-*-cbc` without HMAC, `crypto.createCipher` (removed, no IV) | `crypto.createCipheriv("aes-256-gcm", key, iv)` with a 12-byte random IV, `getAuthTag()` and `setAuthTag()`; `libsodium-wrappers` |
| Random tokens | `Math.random()` | `crypto.randomBytes(32).toString("base64url")`, `crypto.randomUUID()` |
| Password hashing | `createHash("sha256")` | `argon2` package (`argon2.hash(pw, { type: argon2.argon2id })`), `bcrypt`, `crypto.scrypt` |
| MAC check | `===` on strings | `crypto.timingSafeEqual(a, b)` after checking equal length |
| RSA encryption | `RSA_PKCS1_PADDING` | `crypto.publicEncrypt({ key, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING, oaepHash: "sha256" }, data)` |
| TLS client | `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0` | `{ ca: fs.readFileSync("ca.pem") }`, `minVersion: "TLSv1.2"` |
| Browser | `Math.random()` | `crypto.getRandomValues`, `crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, data)` |

## Java and Kotlin

| Need | Avoid | Use |
|---|---|---|
| Symmetric encryption | `Cipher.getInstance("AES")`, `"DES"`, `"AES/ECB/..."`, `"AES/CBC/PKCS5Padding"` without HMAC | `Cipher.getInstance("AES/GCM/NoPadding")` with `new GCMParameterSpec(128, iv)`; Google Tink `Aead` |
| Random tokens | `java.util.Random`, `Math.random()` | `SecureRandom` |
| Password hashing | `MessageDigest.getInstance("SHA-256")` | Spring Security `Argon2PasswordEncoder` or `BCryptPasswordEncoder` |
| MAC check | `Arrays.equals`, `String.equals` | `MessageDigest.isEqual(a, b)` |
| RSA encryption | `"RSA/ECB/PKCS1Padding"`, bare `"RSA"` | `"RSA/ECB/OAEPWithSHA-256AndMGF1Padding"` |
| TLS client | trust-all `X509TrustManager`, `HostnameVerifier` that returns `true` | Default `SSLContext`, or a `KeyStore` with the internal CA loaded into a `TrustManagerFactory` |

## Go

| Need | Avoid | Use |
|---|---|---|
| Symmetric encryption | `cipher.NewCBCEncrypter` without HMAC, custom ECB loops | `aes.NewCipher` then `cipher.NewGCM`, `gcm.Seal(nonce, nonce, plaintext, aad)`; `golang.org/x/crypto/chacha20poly1305` |
| Random tokens | `math/rand` | `crypto/rand` (`rand.Read`) |
| Password hashing | `sha256.Sum256(pw)` | `golang.org/x/crypto/argon2` `IDKey`, `golang.org/x/crypto/bcrypt` |
| MAC check | `bytes.Equal`, `==` | `hmac.Equal`, `subtle.ConstantTimeCompare` |
| RSA | `rsa.EncryptPKCS1v15` | `rsa.EncryptOAEP(sha256.New(), rand.Reader, pub, msg, nil)`, `rsa.SignPSS`, or `crypto/ed25519` |
| TLS | `InsecureSkipVerify: true`, `MinVersion` below 1.2 | `tls.Config{MinVersion: tls.VersionTLS12, RootCAs: pool}` |

## Server and proxy TLS config

| Stack | Setting |
|---|---|
| nginx | `ssl_protocols TLSv1.2 TLSv1.3;` with an ECDHE plus AEAD cipher list from the Mozilla SSL Configuration Generator (intermediate profile) |
| AWS ALB | A TLS 1.2+ policy such as `ELBSecurityPolicy-TLS13-1-2-2021-06` |
| Check | `testssl.sh https://app.example.com`, `sslyze app.example.com` |
