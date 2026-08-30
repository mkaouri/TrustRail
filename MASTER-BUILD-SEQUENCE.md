# TrustRail v0.1 — Master Build Sequence

This is the implementation order for GitHub Copilot.

**Rule:** Complete, test, review, and commit each milestone before starting the next.

---

# Phase 0 — Repository Discipline

## Milestone 0.1 — Initialize Repository

Create:
- `backend/`
- `frontend/`
- `sdk/python/`
- `policies/`
- `examples/refund_agent/`
- `scripts/`
- `.github/workflows/`

Add:
- `.gitignore`
- `.env.example`
- root `docker-compose.yml`

Do not implement business features.

**Commit**
```text
chore: initialize TrustRail repository
```

---

# Phase 1 — Foundation

## Milestone 1 — Backend Skeleton

Implement:
- Python 3.12 project;
- FastAPI app factory/lifecycle;
- settings via environment;
- structured logging;
- request ID middleware;
- `/health`;
- pytest baseline;
- Ruff;
- mypy.

Acceptance:
```http
GET /health
```

returns:

```json
{
  "status": "healthy",
  "service": "trustrail",
  "version": "0.1.0"
}
```

**Copilot prompt**
```text
Use TrustRail Architect to plan Milestone 1.
Then use TrustRail Engineer to implement only Milestone 1.
```

---

## Milestone 2 — PostgreSQL + Alembic

Implement:
- async SQLAlchemy engine/session;
- PostgreSQL Docker service;
- Alembic;
- DB health dependency;
- migration smoke test.

Do not add domain tables yet.

Acceptance:
- clean database can migrate to head;
- backend can connect;
- tests can use isolated DB.

---

## Milestone 3 — OPA Service

Implement:
- OPA Docker service;
- internal Docker network;
- policy client abstraction;
- health/readiness check;
- timeout;
- malformed-response handling;
- fail-closed behavior tests.

Acceptance:
- OPA is not exposed publicly by default;
- backend can evaluate a trivial test policy;
- OPA unavailable never returns ALLOW.

---

# Phase 2 — Identity and Tenant Foundation

## Milestone 4 — Organization Model

Implement:
- organization model;
- repository;
- service;
- schemas;
- migration;
- admin/bootstrap route or CLI suitable for v0.1.

Tests:
- create/read;
- duplicate slug;
- disabled state.

---

## Milestone 5 — API Key Authentication

Implement:
- secure key generation;
- display prefix;
- HMAC/hash verifier;
- server-side pepper;
- expiration;
- revocation;
- authentication dependency.

Critical tests:
- valid key;
- invalid key;
- revoked key;
- expired key;
- raw key never persisted;
- Authorization header never logged.

**Security review gate required.**

---

## Milestone 6 — Agent Registry

Implement:
- model;
- repository;
- service;
- API routes;
- active/disabled state;
- production_authorized flag.

Critical tests:
- tenant A cannot access tenant B agent;
- disabled agent is not considered valid for authorization.

---

# Phase 3 — Policy

## Milestone 7 — Policy Storage and Versioning

Implement:
- policies;
- policy versions;
- immutable version rows;
- SHA-256 checksum;
- activation workflow.

Tests:
- version monotonicity;
- one active version behavior;
- cross-tenant isolation;
- old version not mutated.

---

## Milestone 8 — Refund Rego Policy

Implement sample policy:

```text
0–1000 USD       -> allow
1001–5000 USD    -> requires approval
>5000 USD        -> hard deny
unsupported currency -> hard deny
disabled/non-production-authorized where applicable -> hard deny
```

Add OPA unit tests.

Acceptance:
- policy results are structured, not plain booleans.

---

# Phase 4 — Authorization Core

## Milestone 9 — Universal Action Schema

Implement:
- action request Pydantic model;
- generic action/resource/parameters/context shape;
- canonical request fingerprint;
- idempotency key support design.

Reject invalid:
- negative financial amount;
- malformed currency when refund action;
- oversized or malformed payload.

Avoid baking Stripe-specific fields into the universal model.

---

## Milestone 10 — Deterministic Risk Engine

Implement pure-function risk evaluator.

Initial signals:
- production +10;
- irreversible +25;
- sensitive_data +20;
- external_destination +15;
- near_limit +15;
- high_value +20;
- unusual_hour +10.

Cap 0–100.

Tests:
- each signal;
- combinations;
- cap;
- deterministic repeatability.

---

## Milestone 11 — Decision Engine

Implement as pure application logic.

Precedence:
1. invalid agent -> BLOCK;
2. hard policy deny -> BLOCK;
3. risk >= block threshold -> BLOCK;
4. policy approval required -> ESCALATE;
5. risk >= review threshold -> ESCALATE;
6. policy allow -> ALLOW;
7. unknown -> BLOCK.

Tests must cover every precedence collision.

---

## Milestone 12 — Authorization Persistence

Create:
- action_requests;
- decisions;
- idempotency uniqueness;
- decision history.

Implement:
`POST /v1/actions/authorize`.

Flow:
1. authenticate;
2. resolve tenant;
3. verify agent;
4. persist/request context;
5. evaluate policy;
6. calculate risk;
7. decide;
8. persist immutable decision;
9. return result.

At this milestone, certificates/audit may still be stubbed only if transaction semantics clearly preserve future insertion.

Acceptance:
- refund demo returns ALLOW/ESCALATE/BLOCK correctly;
- repeated idempotent request returns same authoritative action;
- same idempotency key + changed body -> 409.

**Major security review gate required.**

---

# Phase 5 — Evidence

## Milestone 13 — Tamper-Evident Audit Chain

Implement:
- organization-scoped sequence;
- canonical event payload;
- SHA-256 previous/event hash;
- append-only service;
- PostgreSQL advisory transaction lock;
- chain verifier.

Add events for:
- API key create/revoke;
- agent create/disable;
- policy activation;
- authorization decision;
- approval resolution;
- certificate issuance.

Tests:
- valid chain;
- payload mutation;
- previous hash mutation;
- concurrent insert ordering.

---

## Milestone 14 — Action Certificates

Implement:
- Ed25519 signer;
- dev key-loading method;
- key ID;
- canonical payload;
- certificate persistence;
- verification endpoint;
- public-key endpoint.

On successful ALLOW:
- generate signed certificate.

On BLOCK:
- no executable certificate.

On ESCALATE:
- no ALLOW certificate until approval.

Tests:
- valid;
- payload tamper;
- signature tamper;
- unknown key;
- expired;
- wrong action fingerprint.

---

# Phase 6 — Human Control

## Milestone 15 — Approval Workflow

Implement:
- pending approval creation for ESCALATE;
- approval list;
- approve;
- deny;
- row/advisory locking;
- immutable resulting decision;
- fresh ALLOW certificate after approval;
- audit event.

Tests:
- approve once;
- deny once;
- concurrent double resolution;
- tenant isolation;
- original decision unchanged.

**Security review gate required.**

---

# Phase 7 — Developer Experience

## Milestone 16 — Python SDK

Package:

```python
from trustrail import TrustRail

client = TrustRail(api_key="...")

decision = client.authorize(
    agent_id="agt_...",
    action={
        "type": "refund",
        "resource": "payment",
        "parameters": {
            "amount": 200,
            "currency": "USD"
        }
    }
)
```

Convenience:
- `decision.allowed`;
- `decision.requires_approval`;
- `decision.blocked`.

Requirements:
- explicit timeout;
- clear exceptions;
- no silent retries of authorization unless idempotency behavior is preserved.

---

## Milestone 17 — Refund Demo Agent

Create:

```text
examples/refund_agent/
```

Scenarios:

```text
$200     -> ALLOW
$2,800   -> ESCALATE
$18,500  -> BLOCK
```

Demo must show:
- request;
- decision;
- reason;
- certificate when allowed;
- approval workflow when escalated.

---

# Phase 8 — Dashboard

## Milestone 18 — Frontend Skeleton

Create:
- React;
- TypeScript;
- Vite;
- Tailwind;
- typed API client;
- layout/navigation.

Screens:
- Dashboard;
- Agents;
- Actions;
- Approvals;
- Policies;
- Certificates;
- Audit;
- API Keys.

Do not duplicate authorization logic in frontend.

---

## Milestone 19 — Dashboard Core Views

Dashboard:
- action counts;
- ALLOW/ESCALATE/BLOCK;
- recent actions;
- risk score.

Approvals:
- pending list;
- action details;
- approve;
- deny.

Agents:
- create/list/disable.

Policies:
- list/version/activate.

Certificates:
- inspect/verify.

Audit:
- recent events;
- chain verification status.

---

# Phase 9 — CI and Hardening

## Milestone 20 — GitHub Actions

Backend:
```text
ruff
mypy
pytest
docker build
```

OPA:
```text
opa fmt
opa test
```

Frontend:
```text
lint
typecheck
build
```

Also:
- migration test against PostgreSQL service.

---

## Milestone 21 — Security Hardening

Run `TrustRail Security Reviewer`.

Required focus:
- cross-tenant;
- API keys;
- policy bypass;
- OPA outage;
- decision precedence;
- idempotency;
- approval races;
- certificates;
- audit;
- secret scanning.

Do not proceed with unresolved CRITICAL/HIGH authorization issues.

---

# Phase 10 — Deployment

## Milestone 22 — Public Sandbox

Deploy:
- backend;
- PostgreSQL;
- OPA internal;
- frontend;
- HTTPS.

Requirements:
- production debug disabled;
- secure secrets;
- restricted CORS;
- migrations managed;
- health checks;
- backup plan for DB;
- no default/demo admin key exposed.

The first public environment is a **sandbox**, not a production-grade financial control plane.

---

# Phase 11 — Final Alpha Acceptance

TrustRail v0.1 Alpha is complete only when all pass:

## Functional
- organization created;
- agent created;
- API key works;
- policy activated;
- $200 -> ALLOW;
- $2,800 -> ESCALATE;
- $18,500 -> BLOCK;
- human approval changes escalated action through new immutable decision;
- Python SDK works.

## Security
- cross-tenant isolation verified;
- disabled agent never allows;
- OPA down never allows;
- no active policy never allows;
- raw API keys not persisted;
- private signing key not in repository.

## Evidence
- ALLOW certificate verifies;
- modified payload fails;
- modified signature fails;
- audit chain verifies;
- modified audit event breaks verification.

## Engineering
- CI green;
- migrations reproducible;
- Docker Compose starts local stack;
- README setup works from a clean machine.

---

# Recommended Commit Sequence

```text
chore: initialize TrustRail repository
feat: add FastAPI service foundation
feat: add PostgreSQL and migrations
feat: add OPA policy service
feat: add organization registry
security: implement API key authentication
feat: add agent registry
feat: add versioned policy storage
feat: add refund authorization policy
feat: define universal action model
feat: add deterministic risk engine
feat: add decision engine
feat: implement authorization endpoint
feat: add tamper-evident audit chain
feat: add signed action certificates
feat: implement human approval flow
feat: add Python SDK
feat: add refund agent demo
feat: add TrustRail dashboard
ci: add quality and security checks
security: harden v0.1 authorization boundaries
docs: finalize v0.1 alpha
```

---

# Daily Copilot Workflow

For every milestone:

1. Select `TrustRail Architect`.
2. Ask:  
   `Plan Milestone N from MASTER-BUILD-SEQUENCE.md. Do not implement.`
3. Review plan.
4. Select `TrustRail Engineer`.
5. Ask:  
   `Implement Milestone N only, according to the approved plan.`
6. Review diff manually.
7. Run tests.
8. Use `TrustRail Security Reviewer` for security-sensitive milestones.
9. Fix findings one at a time.
10. Commit.
11. Move to next milestone.

Never ask Copilot to "build TrustRail completely."
