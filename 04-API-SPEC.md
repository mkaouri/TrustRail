# TrustRail v0.1 — API Specification

Base path:

```text
/v1
```

Content type:

```text
application/json
```

Authentication:

```http
Authorization: Bearer <TRUSTRAIL_API_KEY>
```

---

## 1. Common Error Format

```json
{
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "The requested resource could not be found.",
    "request_id": "req_..."
  }
}
```

Do not leak cross-tenant resource existence.

---

## 2. Health

### GET /health

Response:

```json
{
  "status": "healthy",
  "service": "trustrail",
  "version": "0.1.0"
}
```

---

## 3. Organizations

### POST /v1/organizations

```json
{
  "name": "Acme Corp",
  "slug": "acme"
}
```

### GET /v1/organizations/{organization_id}

### PATCH /v1/organizations/{organization_id}

Allowed changes in v0.1:
- name;
- status.

---

## 4. Agents

### POST /v1/agents

```json
{
  "name": "refund-agent",
  "description": "Processes customer refunds",
  "agent_type": "financial",
  "production_authorized": true,
  "metadata": {
    "model": "demo",
    "environment": "sandbox"
  }
}
```

Response:

```json
{
  "id": "agt_...",
  "name": "refund-agent",
  "status": "ACTIVE",
  "production_authorized": true,
  "created_at": "2026-08-27T00:00:00Z"
}
```

### GET /v1/agents

Filters:
- status;
- agent_type;
- cursor/limit.

### GET /v1/agents/{agent_id}

### PATCH /v1/agents/{agent_id}

### POST /v1/agents/{agent_id}/disable

---

## 5. API Keys

### POST /v1/api-keys

```json
{
  "name": "refund-agent-key",
  "agent_id": "agt_...",
  "expires_at": null
}
```

Response:

```json
{
  "id": "key_...",
  "prefix": "tr_test_ab12cd",
  "secret": "tr_test_ab12cd...",
  "warning": "This secret will not be shown again."
}
```

### GET /v1/api-keys

Never return key hashes or raw secrets.

### POST /v1/api-keys/{key_id}/revoke

---

## 6. Policies

### POST /v1/policies

```json
{
  "name": "refund-policy",
  "description": "Refund authorization policy",
  "scope": "refund"
}
```

### POST /v1/policies/{policy_id}/versions

```json
{
  "rego_content": "package trustrail.refund\n..."
}
```

The server:
- validates syntax where possible;
- computes checksum;
- creates immutable version.

### POST /v1/policies/{policy_id}/versions/{version}/activate

### GET /v1/policies

### GET /v1/policies/{policy_id}

---

## 7. Authorization

### POST /v1/actions/authorize

Optional header:

```http
Idempotency-Key: <opaque-client-generated-value>
```

Request:

```json
{
  "agent_id": "agt_123",
  "action": {
    "type": "refund",
    "resource": "payment",
    "resource_id": "pay_88991",
    "parameters": {
      "amount": 2800,
      "currency": "USD"
    }
  },
  "context": {
    "customer_verified": true,
    "environment": "production",
    "irreversible": false,
    "external_destination": false,
    "sensitive_data": false
  }
}
```

Response:

```json
{
  "action_id": "act_...",
  "decision_id": "dec_...",
  "decision": "ESCALATE",
  "risk_score": 45,
  "reasons": [
    {
      "code": "HUMAN_APPROVAL_REQUIRED",
      "message": "Refund exceeds the autonomous approval threshold."
    }
  ],
  "approval": {
    "id": "apr_...",
    "status": "PENDING"
  },
  "certificate": null
}
```

ALLOW example:

```json
{
  "action_id": "act_...",
  "decision_id": "dec_...",
  "decision": "ALLOW",
  "risk_score": 10,
  "reasons": [],
  "approval": null,
  "certificate": {
    "id": "cert_...",
    "key_id": "key_2026_001"
  }
}
```

### GET /v1/actions/{action_id}

Returns complete current action view plus immutable decision history.

---

## 8. Approvals

### GET /v1/approvals?status=PENDING

### POST /v1/actions/{action_id}/approve

```json
{
  "reason": "Verified customer escalation."
}
```

Creates a new decision record.

### POST /v1/actions/{action_id}/deny

```json
{
  "reason": "Amount not justified."
}
```

Creates a new `BLOCK` decision record.

Approval endpoints must be idempotent with respect to a resolved approval.

---

## 9. Certificates

### GET /v1/certificates/{certificate_id}

### POST /v1/certificates/verify

```json
{
  "payload": {
    "...": "..."
  },
  "signature": "base64url...",
  "key_id": "key_2026_001"
}
```

Response:

```json
{
  "valid": true,
  "payload_hash": "..."
}
```

### GET /v1/public-keys/{key_id}

Response:

```json
{
  "key_id": "key_2026_001",
  "algorithm": "Ed25519",
  "public_key": "base64url..."
}
```

---

## 10. Audit

### GET /v1/audit/events

Filters:
- event_type;
- entity_type;
- entity_id;
- after sequence;
- limit.

### GET /v1/audit/verify

Response:

```json
{
  "valid": true,
  "checked_events": 1244,
  "first_invalid_sequence": null
}
```

---

## 11. HTTP Behavior

Use:
- `200` successful retrieval;
- `201` creation;
- `202` only when genuinely asynchronous (not needed in core v0.1);
- `400` malformed semantic request;
- `401` missing/invalid authentication;
- `403` authenticated but not permitted;
- `404` resource unavailable to current tenant;
- `409` idempotency conflict or invalid state transition;
- `422` validation errors;
- `503` critical dependency unavailable.

Never convert `503` into implicit authorization.

---

## 12. Reason Codes

Initial stable reason codes:

```text
AGENT_DISABLED
AGENT_NOT_PRODUCTION_AUTHORIZED
NO_ACTIVE_POLICY
POLICY_DENY
AUTONOMOUS_LIMIT_EXCEEDED
MAXIMUM_LIMIT_EXCEEDED
UNSUPPORTED_CURRENCY
RISK_REVIEW_THRESHOLD
RISK_BLOCK_THRESHOLD
HUMAN_APPROVAL_REQUIRED
DEPENDENCY_UNAVAILABLE
INVALID_CONTEXT
```

Reason codes are API contracts. Avoid changing semantics after release.
