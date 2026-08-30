# TrustRail v0.1 — Security Specification

## 1. Security Objective

TrustRail must never authorize an action solely because the system could not determine whether the action was authorized.

Core rule:

> **Uncertainty fails closed.**

---

## 2. Threat Model

Assume an attacker may possess:
- a valid API key for one tenant;
- guessed or leaked UUIDs;
- control over action parameters/context;
- the ability to replay requests;
- the ability to issue concurrent requests;
- the ability to trigger malformed inputs;
- knowledge of API structure.

Assume external dependencies may:
- time out;
- crash;
- return malformed responses.

---

## 3. Key Threats

### Authentication bypass
Mitigation:
- centralized authentication dependency;
- constant-time verifier comparison where applicable;
- strict revoked/expired status checks.

### IDOR / cross-tenant access
Mitigation:
- tenant-scoped repository methods;
- tenant context derived from authenticated principal;
- never trust organization ID supplied by client.

### Policy bypass
Mitigation:
- policy evaluation is mandatory;
- no active policy => BLOCK;
- malformed OPA response => BLOCK;
- hard deny has final precedence.

### Fail-open dependency failure
Mitigation:
- OPA timeout => BLOCK/error;
- DB error => no successful authorization;
- risk-engine exception => BLOCK/error.

### Replay
Mitigation:
- idempotency keys;
- short-lived certificates;
- future nonce support;
- action ID uniqueness.

### Secret leakage
Mitigation:
- no raw API keys at rest;
- no secret logging;
- `.env` ignored;
- private signing key externalized.

### Certificate forgery
Mitigation:
- Ed25519;
- canonical payload encoding;
- explicit key ID;
- signed payload includes decision/action identifiers and expiry.

### Certificate tampering
Mitigation:
- verify payload bytes exactly;
- expose verifier and public key;
- verify expiry separately from signature.

### Audit tampering
Mitigation:
- hash-chained events;
- immutable application API;
- chain verifier;
- organization-scoped sequencing lock.

### Race conditions
Mitigation:
- row/advisory locks for approval resolution and audit sequence;
- unique constraints for idempotency;
- state transitions enforced transactionally.

---

## 4. API Key Design

Format suggestion:

```text
tr_test_<prefix>_<secret>
tr_live_<prefix>_<secret>
```

The database stores:
- environment;
- prefix;
- keyed verifier/hash;
- status;
- expiration.

Preferred verifier:
- HMAC-SHA256 using a server-side pepper, or
- a strong password/key hash if deliberately selected.

Because API keys should contain high entropy, HMAC-SHA256 with a protected server-side pepper is acceptable and efficient for v0.1.

Never use the display prefix as authentication.

---

## 5. Signing Keys

v0.1:
- generate Ed25519 key pair;
- store private key in a mounted secret/environment-specific secret file;
- store public metadata in application config/database;
- include `key_id` in certificates.

Never:
- commit private key;
- log private key;
- return private key through API.

Later:
- migrate signing to KMS/HSM;
- support rotation and retired verification keys.

---

## 6. Canonicalization

All hashes/signatures over JSON must use deterministic canonical serialization.

Rules:
- UTF-8;
- stable key ordering;
- no insignificant whitespace;
- deterministic numbers/booleans/null;
- no timestamps generated during verification.

Prefer a well-defined canonical JSON function used in exactly one shared module.

---

## 7. Logging

Allowed:
- request ID;
- action ID;
- agent ID;
- organization ID;
- decision;
- reason codes;
- latency;
- dependency status.

Disallowed by default:
- API key;
- Authorization header;
- signing private key;
- passwords;
- OAuth tokens;
- full customer PII;
- arbitrary raw action payload.

---

## 8. Security Headers / API Hardening

For deployed frontend/API:
- HTTPS only;
- HSTS where appropriate;
- restrictive CORS;
- request size limits;
- secure headers;
- rate limiting at edge/reverse proxy later;
- no debug tracebacks in public responses.

---

## 9. Approval Security

Approvals are sensitive.

Requirements:
- authenticated admin/reviewer principal;
- same-tenant verification;
- only PENDING approval can transition;
- transaction lock before resolving;
- original decision remains immutable;
- approval/denial creates audit event;
- resulting decision links to approval context.

---

## 10. Security Test Matrix

Mandatory automated tests:

- invalid API key rejected;
- revoked API key rejected;
- expired API key rejected;
- API key from tenant A cannot access tenant B agent;
- tenant A cannot infer tenant B resource existence;
- disabled agent never ALLOW;
- no policy never ALLOW;
- OPA down never ALLOW;
- malformed OPA response never ALLOW;
- negative/invalid amount rejected;
- idempotency replay returns same action;
- same idempotency key + changed payload conflicts;
- certificate mutation fails verification;
- signature mutation fails verification;
- expired certificate not accepted as executable evidence;
- audit mutation fails chain verification;
- concurrent approval resolves once;
- concurrent audit writes preserve chain.

---

## 11. Security Review Gate

Before any public sandbox deployment, run:
- dependency vulnerability scan;
- secret scan;
- static lint/type/test pipeline;
- manual cross-tenant review;
- hostile authorization review;
- certificate test vectors;
- audit concurrency tests.

A public deployment is blocked by unresolved CRITICAL or HIGH authorization findings.
