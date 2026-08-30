# TrustRail v0.1 — Action Certificate Specification

## 1. Purpose

A TrustRail Action Certificate is cryptographic evidence that TrustRail evaluated a specific action under a specific policy/risk context and produced a specific decision.

It is **not** proof that the external action actually succeeded.

---

## 2. Algorithm

v0.1 signing algorithm:

```text
Ed25519
```

Payload hashing:

```text
SHA-256
```

Encoding:
- canonical JSON UTF-8 bytes;
- Base64URL for signature/public key serialization where appropriate.

---

## 3. Certificate Payload

Required fields:

```json
{
  "schema": "trustrail.action-certificate",
  "version": "0.1",
  "certificate_id": "cert_...",
  "action_id": "act_...",
  "decision_id": "dec_...",
  "organization_id": "org_...",
  "agent_id": "agt_...",
  "action_type": "refund",
  "resource_type": "payment",
  "resource_id": "pay_...",
  "decision": "ALLOW",
  "risk_score": 12,
  "policy": [
    {
      "policy_id": "pol_...",
      "version": 3,
      "checksum": "..."
    }
  ],
  "issued_at": "2026-08-27T12:00:00Z",
  "expires_at": "2026-08-27T12:05:00Z",
  "key_id": "signing_2026_001"
}
```

Do not include secrets.

For sensitive parameters, do not place raw values in the public certificate unless required.
Instead include a request/action fingerprint.

Recommended additional field:

```json
{
  "action_fingerprint": "sha256:..."
}
```

---

## 4. Canonicalization

Use one shared canonical serializer.

Concept:

```python
canonical = json.dumps(
    payload,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False
).encode("utf-8")
```

If a formal JSON canonicalization standard is adopted later, version the certificate schema.

---

## 5. Signing

```text
payload_bytes = canonicalize(payload)
payload_hash  = SHA256(payload_bytes)
signature     = Ed25519.sign(payload_bytes)
```

Persist:
- payload;
- payload hash;
- signature;
- key ID.

---

## 6. Verification

Verification steps:

1. validate certificate schema/version;
2. locate public key by `key_id`;
3. canonicalize payload;
4. verify Ed25519 signature;
5. compare derived payload hash if present;
6. evaluate expiry;
7. optionally compare action fingerprint to intended action.

Return separate concepts:
- `signature_valid`;
- `expired`;
- `valid_for_use`.

A mathematically valid signature on an expired certificate should not automatically authorize execution.

---

## 7. Lifetime

Initial recommendation:
- action authorization certificate TTL: 5 minutes for demo financial actions;
- configurable by action category later.

Approval-generated ALLOW certificate receives a fresh issue time.

---

## 8. Key Rotation

v0.1 data model must support:
- multiple public keys;
- active signing key;
- retired verification keys.

Old public keys must remain available long enough to verify retained certificates.

---

## 9. Tamper Demo

Demo procedure:
1. authorize $200 refund;
2. export certificate;
3. verify => valid;
4. change payload to $20,000 or alter fingerprint;
5. verify => invalid.

This demo is a required v0.1 acceptance scenario.

---

## 10. Security Notes

A certificate proves TrustRail's signed statement.
It does not prove:
- execution occurred;
- execution succeeded;
- downstream system honored the certificate;
- caller did not request another authorization later.

Execution-attestation belongs to a future protocol.
