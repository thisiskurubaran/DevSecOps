# Rotation runbook

Copy this template into the incident or ticket for each leaked credential. Fill it in as you go. Do not paste the secret value anywhere in it.

```markdown
## Rotation: <secret name / type>

- Detected: YYYY-MM-DD HH:MM UTC, by <tool or person>
- Location: <repo>/<file>:<line>, commit <sha>, pushed to <remote> at <time>
- Exposure: public repo / private repo / CI log / ticket / chat
- Scope of credential: <what it can do>
- Owner: <team or person>

### Steps
- [ ] New credential issued (time: )
- [ ] Stored in <secrets manager path>
- [ ] Consumers updated: <service list>
- [ ] Consumers verified healthy
- [ ] Old credential revoked (time: )
- [ ] Provider audit logs checked from <leak time> to <revoke time>
- [ ] Suspicious activity found? yes / no. If yes, escalate to incident-response.
- [ ] Code changed to read from store (PR: )
- [ ] History cleaned (only if needed, with owner approval)
- [ ] Prevention added (pre-commit, CI scan, push protection)
```

## Provider notes

Check each provider's current docs. Console paths change.

### AWS access keys

1. `aws iam create-access-key --user-name <user>` (or better, replace with a role and drop static keys).
2. Update consumers.
3. `aws iam update-access-key --access-key-id <old> --status Inactive --user-name <user>`, watch for errors, then `aws iam delete-access-key`.
4. Check usage: `aws iam get-access-key-last-used --access-key-id <old>`, and CloudTrail `lookup-events --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=<old>`.
5. If AWS opened a support case or attached `AWSCompromisedKeyQuarantine`, follow it.

### GitHub tokens

- Personal access tokens: revoke in Settings, Developer settings. Prefer fine-grained tokens with repo scope and expiry.
- GitHub App private keys: generate a new key, deploy, delete the old key in the app settings.
- Review the org audit log for actions by the token.

### Database passwords

- Postgres: `ALTER ROLE app_user WITH PASSWORD '<new>';` during a window where the app can read either. Safer: create `app_user_v2`, switch the app, then drop the old role.
- Long term: Vault database secrets engine issues per-lease users and revokes them on expiry.

### Stripe, Twilio, SendGrid and similar API keys

- Roll the key in the provider dashboard. Many providers offer a grace period where both keys work. Use it to deploy, then expire the old key.
- Check the provider's request logs for unknown IPs.

### Private keys and certificates (TLS, SSH, signing)

- TLS: issue a new cert with a new key, deploy, then revoke the old cert with the CA.
- SSH: remove the old public key from `authorized_keys`, GitHub deploy keys, and bastion configs.
- Signing keys (JWT, cosign, GPG): publish the new key in JWKS or keyring first, switch signing, keep the old public key for verification until old tokens expire, then remove it.

### Cloud KMS keys

- KMS keys are not secrets you copy around. If a key policy was too open, fix the policy. Rotation (`aws kms enable-key-rotation`) makes new key material for new encryptions, and old ciphertext still decrypts.

## History cleanup

Only after rotation. A cleaned history does not un-leak a key someone already cloned.

```sh
# replacements.txt holds one line per secret: <literal>==>REMOVED
git filter-repo --replace-text replacements.txt
git push --force --all && git push --force --tags
```

Tell every contributor to re-clone. Old forks and PR refs on GitHub may still hold the commit until GitHub support purges them.
