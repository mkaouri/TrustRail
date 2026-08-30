# TrustRail v0.1 — Database Specification

## 1. Database

PostgreSQL is the authoritative datastore.

Use:
- UUID primary keys internally unless strong reason otherwise;
- timezone-aware UTC timestamps;
- JSONB for flexible action/context payloads;
- explicit foreign keys;
- unique constraints for tenant-scoped names where useful;
- indexes on common filters.

Externally exposed identifiers may use prefixed IDs derived from UUID values in the application layer.

---

## 2. Tables

### organizations

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR(200) | required |
| slug | VARCHAR(100) | unique |
| status | enum | ACTIVE, DISABLED |
| created_at | timestamptz | required |
| updated_at | timestamptz | required |

### agents

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | required |
| name | VARCHAR(200) | |
| description | TEXT | nullable |
| agent_type | VARCHAR(100) | |
| status | enum | ACTIVE, DISABLED |
| metadata | JSONB | default `{}` |
| production_authorized | BOOLEAN | default false |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Index:
`(organization_id, status)`.

### api_keys

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | required |
| agent_id | UUID FK nullable | null = org/admin key |
| name | VARCHAR(120) | |
| key_prefix | VARCHAR(32) | for display |
| key_hash | VARCHAR/TEXT | verifier only |
| status | enum | ACTIVE, REVOKED |
| expires_at | timestamptz nullable | |
| last_used_at | timestamptz nullable | |
| created_at | timestamptz | |
| revoked_at | timestamptz nullable | |

Never persist the raw key.

### policies

| Column | Type |
|---|---|
| id | UUID PK |
| organization_id | UUID FK |
| name | VARCHAR(200) |
| description | TEXT nullable |
| scope | VARCHAR(120) |
| status | enum |
| created_at | timestamptz |

Unique recommended:
`organization_id + name`.

### policy_versions

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| policy_id | UUID FK | |
| version | INTEGER | monotonic |
| rego_content | TEXT | |
| checksum | VARCHAR(64) | SHA-256 |
| is_active | BOOLEAN | |
| created_at | timestamptz | |
| activated_at | timestamptz nullable | |

Unique:
`policy_id + version`.

Only one active version per policy; enforce in service and with an appropriate partial unique index if practical.

### action_requests

| Column | Type |
|---|---|
| id | UUID PK |
| organization_id | UUID FK |
| agent_id | UUID FK |
| action_type | VARCHAR(120) |
| resource_type | VARCHAR(120) |
| resource_id | VARCHAR(255) nullable |
| parameters | JSONB |
| context | JSONB |
| idempotency_key | VARCHAR(255) nullable |
| request_fingerprint | VARCHAR(64) |
| requested_at | timestamptz |

Unique:
`organization_id + idempotency_key` when idempotency_key is not null.

### decisions

Historical and immutable.

| Column | Type |
|---|---|
| id | UUID PK |
| action_request_id | UUID FK |
| decision_sequence | INTEGER |
| outcome | enum(ALLOW, ESCALATE, BLOCK) |
| risk_score | SMALLINT |
| trust_score | SMALLINT nullable |
| policy_result | JSONB |
| risk_signals | JSONB |
| reasons | JSONB |
| decision_source | VARCHAR(80) |
| created_at | timestamptz |

Unique:
`action_request_id + decision_sequence`.

Do not update historical decision rows.

### approvals

| Column | Type |
|---|---|
| id | UUID PK |
| action_request_id | UUID FK |
| status | enum(PENDING, APPROVED, DENIED, EXPIRED) |
| reviewer_principal | VARCHAR(255) nullable |
| reason | TEXT nullable |
| created_at | timestamptz |
| resolved_at | timestamptz nullable |

### action_certificates

| Column | Type |
|---|---|
| id | UUID PK |
| decision_id | UUID FK unique |
| certificate_version | VARCHAR(20) |
| certificate_payload | JSONB |
| payload_hash | VARCHAR(64) |
| signature | TEXT |
| key_id | VARCHAR(120) |
| expires_at | timestamptz nullable |
| created_at | timestamptz |

Certificates are immutable.

### audit_events

| Column | Type |
|---|---|
| id | UUID PK |
| organization_id | UUID FK |
| sequence | BIGINT |
| event_type | VARCHAR(120) |
| entity_type | VARCHAR(120) |
| entity_id | VARCHAR(255) |
| payload | JSONB |
| previous_hash | VARCHAR(64) nullable |
| event_hash | VARCHAR(64) |
| created_at | timestamptz |

Unique:
`organization_id + sequence`.

The chain is organization-scoped.

---

## 3. Audit Concurrency

To avoid two concurrent events using the same `previous_hash`:

Recommended v0.1 method:
1. open DB transaction;
2. acquire organization-level PostgreSQL advisory transaction lock;
3. select latest audit event;
4. calculate next sequence/hash;
5. insert;
6. commit.

This is simple and sufficient for v0.1.

---

## 4. Tenant Isolation

Every repository method for tenant-owned data must receive `organization_id`.

Bad:

```python
get_agent(agent_id)
```

Preferred:

```python
get_agent(organization_id, agent_id)
```

Cross-tenant behavior should not leak whether another tenant's resource exists.

---

## 5. Delete Strategy

Security-relevant evidence:
- action requests;
- decisions;
- approvals;
- certificates;
- audit events;

must not be deleted through normal application APIs.

For mutable configuration entities:
- organizations;
- agents;
- policies;
- API keys;

use lifecycle status/revocation instead of destructive deletion wherever practical.

---

## 6. Migration Rules

- all schema changes through Alembic;
- never modify an already-applied migration;
- use explicit downgrade where safe;
- run migrations in CI against a fresh database;
- include data migration plan when changing decision/certificate semantics.

---

## 7. Seed Data for Demo

Development seed:
- organization: `TrustRail Demo`;
- agent: `refund-agent`;
- sample refund policy;
- development admin API key emitted only during seed command;
- no production secrets.
