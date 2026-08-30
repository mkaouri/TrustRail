# TrustRail v0.1 — Decision Engine Specification

## 1. Purpose

The Decision Engine combines:
- identity/agent validity;
- policy evaluation;
- deterministic risk evaluation;

into one final outcome:

```text
ALLOW
ESCALATE
BLOCK
```

The Decision Engine itself must contain no external I/O.

---

## 2. Inputs

```python
DecisionInput(
    agent_state,
    policy_evaluation,
    risk_evaluation,
    context
)
```

### Agent State
At minimum:
- exists;
- active;
- belongs to authenticated organization;
- production authorized when required.

### Policy Evaluation

Example:

```json
{
  "allow": false,
  "requires_approval": true,
  "hard_deny": false,
  "reasons": [
    "AUTONOMOUS_LIMIT_EXCEEDED"
  ],
  "metadata": {
    "policy_id": "pol_...",
    "policy_version": 3
  }
}
```

### Risk Evaluation

```json
{
  "score": 45,
  "signals": [
    {
      "code": "HIGH_VALUE",
      "points": 20
    }
  ]
}
```

---

## 3. Decision Precedence

Strict precedence:

1. invalid authentication / tenant mismatch -> reject transport request;
2. disabled/invalid agent -> BLOCK;
3. hard policy deny -> BLOCK;
4. policy requires approval -> ESCALATE unless a hard risk block is triggered;
5. risk score >= block threshold -> BLOCK;
6. risk score >= review threshold -> ESCALATE;
7. policy allow -> ALLOW;
8. anything unrecognized -> BLOCK.

Reference pseudocode:

```python
def decide(input: DecisionInput) -> DecisionResult:
    if not input.agent_state.valid:
        return block("AGENT_INVALID")

    if input.policy.hard_deny:
        return block(*input.policy.reasons)

    if input.risk.score >= input.thresholds.block:
        return block("RISK_BLOCK_THRESHOLD", *input.policy.reasons)

    if input.policy.requires_approval:
        return escalate("HUMAN_APPROVAL_REQUIRED", *input.policy.reasons)

    if input.risk.score >= input.thresholds.review:
        return escalate("RISK_REVIEW_THRESHOLD")

    if input.policy.allow:
        return allow()

    return block("UNDETERMINED_AUTHORIZATION")
```

---

## 4. Initial Risk Model

Defaults:

```text
review_threshold = 40
block_threshold = 70
```

Example signals:

| Signal | Points |
|---|---:|
| production environment | +10 |
| irreversible operation | +25 |
| sensitive data | +20 |
| external destination | +15 |
| amount >= 80% autonomous limit | +15 |
| high transaction amount | +20 |
| unusual execution hour | +10 |

Cap score to `[0, 100]`.

The risk engine must return reasons/signals, not only a number.

---

## 5. Policy vs Risk

Policy:
- determines whether the action is authorized by rule.

Risk:
- determines whether context makes an otherwise permitted action dangerous.

Example:

Policy says refund <= 1000 is permitted.

A 900 USD refund:
- policy: allow;
- but context: external destination + sensitive data + irreversible;
- risk may force escalation/block.

Risk can tighten a policy result.
Risk must never loosen a hard policy deny.

---

## 6. Human Approval

An `ESCALATE` decision creates a pending approval.

On approval:
- create a new decision row with sequence +1;
- outcome may become `ALLOW`;
- include reason `HUMAN_APPROVED`;
- generate a new certificate;
- append audit event.

On denial:
- create a new `BLOCK` decision;
- append audit event.

Never mutate the original escalated decision.

---

## 7. Explainability

Every non-ALLOW outcome must return at least one stable reason code.

Optional human-readable messages are presentation aids and may evolve.

Machine consumers should rely on:
- decision;
- reason codes;
- certificate validity;
- IDs.

---

## 8. Unit Tests

Required:
- hard deny beats low risk;
- hard deny beats approval-required;
- risk block beats approval-required;
- approval-required beats low-risk allow;
- risk review escalates permitted action;
- low-risk policy allow permits action;
- unknown policy result blocks;
- risk score clamped;
- deterministic repeated inputs yield identical outputs.
