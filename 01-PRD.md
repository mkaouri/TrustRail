# TrustRail v0.1 — Product Requirements Document

**Status:** Alpha specification  
**Version:** 0.1.0  
**Product:** TrustRail  
**Primary objective:** Provide a deterministic authorization layer for autonomous AI-agent actions.

---

## 1. Product Vision

TrustRail is a neutral control plane that sits between an AI agent and any consequential external action.

The v0.1 product must answer one question reliably:

> **Should this agent be allowed to perform this exact action, right now, under the currently active policy and risk context?**

For every authorization request TrustRail returns exactly one decision:

- `ALLOW`
- `ESCALATE`
- `BLOCK`

TrustRail must also produce an auditable record of how that decision was reached and, for successful authorization decisions, a signed Action Certificate.

---

## 2. v0.1 Goals

TrustRail v0.1 must:

1. Register organizations.
2. Register AI agents under an organization.
3. Issue API keys to organizations and agents.
4. Store versioned authorization policies.
5. Evaluate agent actions using OPA/Rego.
6. Calculate deterministic risk signals in application code.
7. Produce `ALLOW`, `ESCALATE`, or `BLOCK`.
8. Persist immutable authorization records.
9. Generate tamper-evident audit events.
10. Generate Ed25519-signed Action Certificates.
11. Support human approval for escalated actions.
12. Expose a Python SDK.
13. Provide a minimal admin dashboard.
14. Provide a simulated refund-agent demo.
15. Run fully in Docker Compose for local development.
16. Run automated CI checks in GitHub Actions.

---

## 3. Non-Goals

TrustRail v0.1 will **not** include:

- autonomous insurance underwriting;
- blockchain;
- a custom LLM;
- ML-based final authorization;
- Kafka;
- Kubernetes;
- Redis unless a concrete v0.1 need appears;
- enterprise SSO/SAML;
- mobile apps;
- complex billing;
- dozens of SaaS integrations;
- production payment execution;
- production-grade multi-region deployment;
- full MCP/A2A implementation.

The purpose of v0.1 is to prove the TrustRail authorization primitive.

---

## 4. Target Users

### 4.1 Developer
Integrates an AI agent with TrustRail before tool execution.

Needs:
- simple API;
- clear SDK;
- deterministic response;
- useful reason codes;
- easy local setup.

### 4.2 Security / Risk Administrator
Defines policies and reviews blocked/escalated actions.

Needs:
- strong auditability;
- immutable records;
- explainable decisions;
- agent and key management.

### 4.3 Human Approver
Approves or denies an escalated action.

Needs:
- action context;
- risk reasons;
- policy reasons;
- explicit approve/deny controls.

---

## 5. Core User Journey

1. Organization is created.
2. Administrator registers an agent.
3. TrustRail generates an API key and displays its secret once.
4. Administrator activates a policy.
5. Agent prepares an external action.
6. Agent calls `POST /v1/actions/authorize`.
7. TrustRail authenticates the caller.
8. TrustRail verifies tenant and agent ownership.
9. OPA evaluates authorization policy.
10. Risk Engine calculates deterministic signals.
11. Decision Engine produces `ALLOW`, `ESCALATE`, or `BLOCK`.
12. TrustRail persists the immutable decision.
13. TrustRail appends a tamper-evident audit event.
14. TrustRail signs a certificate when applicable.
15. Agent receives the result.
16. If escalated, an authorized human approves or denies it.
17. The approval creates new evidence; it does not overwrite history.

---

## 6. Core Functional Requirements

### FR-001 Organization Registry
The system shall support create, retrieve, update-status, and list operations for organizations.

### FR-002 Agent Registry
Each agent shall:
- belong to exactly one organization;
- have an external UUID-style identifier;
- have `ACTIVE` or `DISABLED` status;
- contain metadata that is non-authoritative.

### FR-003 API Keys
The system shall:
- generate cryptographically secure keys;
- return the full secret exactly once;
- store only a verifier/hash;
- support revoke and rotate;
- associate keys with an organization and optionally an agent.

### FR-004 Policies
The system shall:
- store policies by organization;
- support immutable versions;
- allow exactly one active version per logical policy scope where applicable;
- checksum policy content;
- evaluate policy using OPA.

### FR-005 Universal Action Envelope
Every authorization request shall contain:
- `agent_id`;
- action type;
- resource type;
- optional resource ID;
- structured parameters;
- structured context;
- optional idempotency key.

### FR-006 Decision
Every authorization shall end as exactly:
- `ALLOW`;
- `ESCALATE`;
- `BLOCK`.

No ambiguous state is allowed.

### FR-007 Fail Closed
Any uncertainty in identity, tenant ownership, policy availability, policy validity, or required authorization data shall result in denial of execution.

API transport failures may use appropriate HTTP errors, but the caller must never interpret failure as permission to execute.

### FR-008 Risk Engine
Risk must be deterministic in v0.1.

Example signals:
- production environment;
- high-value transaction;
- near-policy-limit behavior;
- irreversible action;
- external destination;
- unusual execution time;
- sensitive-data flag.

### FR-009 Approval Workflow
For `ESCALATE`:
- create a pending approval;
- allow authorized reviewer to approve or deny;
- retain original decision;
- append new events instead of updating history.

### FR-010 Certificates
TrustRail shall sign canonical certificate payloads using Ed25519.

### FR-011 Audit Chain
Each audit event shall contain:
- previous hash;
- canonical payload;
- event hash.

The system shall expose chain verification.

### FR-012 Python SDK
The SDK shall support:
- API key configuration;
- authorization;
- decision convenience properties;
- certificate verification helper when feasible.

### FR-013 Dashboard
Minimal screens:
- Dashboard;
- Agents;
- Actions;
- Approvals;
- Policies;
- API Keys;
- Certificates;
- Audit.

---

## 7. Non-Functional Requirements

### Security
- deny by default;
- strong tenant isolation;
- no plaintext API keys at rest;
- no signing private key in source control;
- no sensitive secrets in logs;
- immutable decision and audit history;
- input validation on all untrusted data.

### Reliability
- authorization path must be deterministic;
- OPA unavailable => authorization fails closed;
- database write failure => caller does not receive a successful authorization.

### Performance
v0.1 target:
- local p95 authorization latency under 250 ms excluding cold startup;
- no unnecessary LLM calls;
- one OPA evaluation per authorization unless explicitly optimized later.

### Observability
Log:
- correlation/request ID;
- organization ID;
- agent ID;
- action ID;
- final decision;
- latency.

Do not log:
- API key secrets;
- signing private keys;
- passwords;
- external access tokens;
- raw confidential payloads unless explicitly configured.

---

## 8. Initial Demo Policy

Refund agent:

| Amount | Result |
|---:|---|
| 0–1,000 USD | ALLOW, subject to risk rules |
| 1,001–5,000 USD | ESCALATE |
| >5,000 USD | BLOCK |

Additional rules:
- disabled agent => BLOCK;
- unsupported currency => BLOCK;
- missing policy => BLOCK;
- production context requires production-authorized agent.

---

## 9. Definition of Done

TrustRail v0.1 Alpha is complete when:

- all core API routes exist;
- Docker Compose starts backend + PostgreSQL + OPA;
- migrations run cleanly;
- refund demo produces ALLOW / ESCALATE / BLOCK;
- signed certificates verify and fail after tampering;
- audit-chain verification detects modification;
- cross-tenant tests pass;
- API-key tests pass;
- fail-closed tests pass;
- Python SDK can call a running TrustRail instance;
- dashboard can inspect actions and resolve approvals;
- CI passes Ruff, mypy, pytest, OPA tests, frontend checks, and Docker build.

---

## 10. Product Success Criteria for v0.1

The first external technical user should be able to:

1. clone the repository;
2. run Docker Compose;
3. create an organization;
4. register an agent;
5. receive an API key;
6. activate the sample refund policy;
7. call authorization from Python in less than 30 minutes;
8. understand why every decision was made.
