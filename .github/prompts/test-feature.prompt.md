---
description: Generate and strengthen tests for a TrustRail feature
agent: TrustRail Engineer
---

Review the requested feature and its existing tests.

Add missing tests with emphasis on security boundaries and fail-closed behavior.

For tenant-owned resources include:
- same-tenant success;
- cross-tenant denial;
- disabled/revoked state;
- non-existent resource without information leakage.

For authorization include:
- ALLOW;
- ESCALATE;
- BLOCK;
- malformed input;
- missing policy;
- dependency unavailable;
- deterministic repeatability.

For idempotency include:
- same key + same payload returns same authorization;
- same key + different payload returns conflict;
- concurrent duplicate requests do not create multiple authoritative actions.

For certificates include:
- valid signature;
- payload tamper;
- signature tamper;
- unknown key;
- expiry.

For audit include:
- valid chain;
- altered event;
- broken previous hash;
- concurrent append ordering.

Do not weaken existing assertions.
Run the appropriate test suite after changes and report results.
