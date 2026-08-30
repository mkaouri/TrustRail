# TrustRail v0.1 — Architecture

## 1. Architecture Principles

TrustRail is security-critical authorization infrastructure.

The v0.1 architecture prioritizes:

1. deterministic behavior;
2. fail-closed authorization;
3. strict tenant isolation;
4. auditability;
5. separation of policy, risk, and execution;
6. replaceable components;
7. minimal infrastructure.

---

## 2. Logical Architecture

```text
AI Agent / Client
       |
       v
Python SDK / REST
       |
       v
FastAPI Gateway
       |
       +--> Authentication / Tenant Resolution
       |
       +--> Agent Registry
       |
       +--> Policy Service ------> OPA
       |
       +--> Risk Engine
       |
       +--> Decision Engine
       |
       +--> Certificate Service --> Ed25519
       |
       +--> Audit Service
       |
       v
PostgreSQL
```

TrustRail never executes the external business action in v0.1.
It authorizes or denies the action and returns evidence.

---

## 3. Backend Layering

```text
app/
  api/            # HTTP route handlers
  core/           # settings, errors, lifecycle, logging
  models/         # SQLAlchemy models
  schemas/        # Pydantic request/response contracts
  repositories/   # database access
  services/       # orchestration and business logic
  security/       # API keys, signatures, hashing
  policy/         # OPA client/adapters
  risk/           # deterministic risk signals
```

Rules:
- routes perform transport concerns only;
- services own business behavior;
- repositories own persistence;
- OPA access is isolated behind a policy client interface;
- signing is isolated behind a certificate signer interface.

---

## 4. Recommended Repository Layout

```text
trustrail/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── security/
│   │   ├── policy/
│   │   ├── risk/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
├── sdk/
│   └── python/
├── policies/
│   ├── refund.rego
│   └── tests/
├── examples/
│   └── refund_agent/
├── docs/
├── scripts/
├── .github/
│   ├── agents/
│   ├── prompts/
│   └── workflows/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 5. Runtime Components

### FastAPI
Responsibilities:
- request validation;
- auth extraction;
- tenant context;
- route dispatch;
- standardized errors.

### PostgreSQL
System of record for:
- organizations;
- agents;
- API key verifiers;
- policy metadata;
- policy versions;
- action requests;
- decisions;
- approvals;
- certificates;
- audit events.

### OPA
Responsibilities:
- evaluate declarative authorization policy;
- return structured policy result;
- never access the database directly;
- receive all needed context from TrustRail.

### Frontend
Read-oriented first.
Mutations are limited to:
- agent management;
- policy management;
- API key management;
- approval decision.

### Python SDK
A thin, dependable client.
No hidden policy behavior inside the SDK.

---

## 6. Authorization Sequence

```text
Client
  |
  | POST /v1/actions/authorize
  v
API
  |
  | authenticate API key
  v
Tenant Context
  |
  | verify agent belongs to tenant
  v
Agent Service
  |
  | load active policies
  v
Policy Service ---> OPA
  |
  | structured policy result
  v
Risk Engine
  |
  | risk signals + score
  v
Decision Engine
  |
  | ALLOW / ESCALATE / BLOCK
  v
Persistence Transaction
  |-- action request
  |-- decision
  |-- approval if needed
  |-- certificate if applicable
  |-- audit event
  v
Response
```

Critical rule:
A caller must not receive `ALLOW` until the authoritative record and certificate have been persisted successfully.

---

## 7. Failure Model

| Failure | Behavior |
|---|---|
| invalid API key | reject request |
| disabled API key | reject request |
| unknown agent | BLOCK or 404 according to API contract; never ALLOW |
| cross-tenant agent | reject without leaking resource existence |
| no active policy | BLOCK |
| malformed policy | BLOCK |
| OPA unavailable | BLOCK |
| risk engine error | BLOCK |
| certificate signing error on required certificate | BLOCK / fail request |
| database commit failure | fail request; no successful authorization |
| audit chain failure | fail authorization transaction |

---

## 8. Transactions and Consistency

Authorization record creation should use one database transaction where practical.

The transaction should atomically persist:
- action request;
- decision;
- pending approval when needed;
- certificate metadata when generated;
- audit event.

If signing occurs outside the DB transaction, design compensation carefully. For v0.1, prefer generating the certificate payload/signature in memory before commit and persisting it in the same transaction.

---

## 9. Idempotency

`POST /v1/actions/authorize` accepts an idempotency key.

Uniqueness scope:
`organization_id + idempotency_key`.

Repeated matching request:
- return the existing authorization result.

Repeated key with materially different request:
- return conflict.

Persist a request fingerprint derived from canonical input.

---

## 10. Security Boundaries

Trust boundaries:
1. client -> API;
2. API -> database;
3. API -> OPA;
4. certificate signer private key.

OPA should not be internet-exposed in local/prod designs.

Signing keys should be loaded from a secret provider/environment in v0.1 and later migrated to KMS/HSM.

---

## 11. Future-Compatible Interfaces

Design interfaces so later versions can replace components:

```python
class PolicyEvaluator(Protocol):
    async def evaluate(self, input: PolicyInput) -> PolicyEvaluation: ...

class RiskEvaluator(Protocol):
    async def evaluate(self, action: ActionContext) -> RiskEvaluation: ...

class CertificateSigner(Protocol):
    def sign(self, payload: bytes) -> SignatureResult: ...
```

Potential future implementations:
- OPA sidecar;
- embedded WASM policy;
- cloud policy service;
- ML-assisted risk;
- KMS/HSM signer.

---

## 12. Architectural Anti-Patterns

Do not:
- put authorization SQL in FastAPI routes;
- let frontend calculate decisions;
- let the SDK override server decisions;
- use an LLM as the final authorization authority;
- store plaintext secrets;
- mutate historical decisions;
- combine policy rules and risk heuristics into one opaque score;
- return ALLOW on dependency timeout.
