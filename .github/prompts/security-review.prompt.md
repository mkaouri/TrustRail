---
description: Run a hostile TrustRail security review
agent: TrustRail Security Reviewer
---

Perform a hostile security review of the current TrustRail implementation.

Assume an attacker has:
- a valid API key for another tenant;
- arbitrary action JSON control;
- guessed UUIDs;
- replay capability;
- concurrency capability.

Attempt to find ways to:
- impersonate another agent;
- access another organization;
- force ALLOW;
- bypass or confuse OPA;
- lower risk improperly;
- approve the same action twice;
- reuse idempotency keys maliciously;
- forge or replay certificates;
- mutate audit history;
- obtain secrets;
- exploit dependency failure.

Do not modify code.

Provide only concrete findings with:
- severity;
- file/function;
- exploit scenario;
- impact;
- remediation;
- regression test.

Conclude with one of:
- `SECURITY GATE: PASS`
- `SECURITY GATE: FAIL`

Any unresolved CRITICAL or HIGH authorization issue => FAIL.
