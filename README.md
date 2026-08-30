# TrustRail v0.1 GitHub Copilot Development Pack

TrustRail is a deterministic authorization and evidence layer for autonomous AI-agent actions.

This repository pack contains the specifications and Copilot instructions needed to build the first TrustRail alpha in VS Code with GitHub Copilot.

---

## Core Product Contract

```text
AI Agent
   |
   v
TrustRail
   |
   +--> Identity / Agent State
   +--> OPA Policy
   +--> Deterministic Risk
   |
   v
ALLOW / ESCALATE / BLOCK
   |
   +--> Signed Action Certificate
   +--> Tamper-Evident Audit Trail
```

TrustRail v0.1 does **not** execute the external business action.
It authorizes the action and returns evidence.

---

## Pack Contents

1. `01-PRD.md` — product scope and requirements
2. `02-ARCHITECTURE.md` — technical architecture
3. `03-DATABASE.md` — database model
4. `04-API-SPEC.md` — REST API contract
5. `05-SECURITY.md` — threat model and security controls
6. `06-DECISION-ENGINE.md` — ALLOW / ESCALATE / BLOCK rules
7. `07-CERTIFICATE-SPEC.md` — Action Certificate format
8. `.github/copilot-instructions.md` — repository-wide Copilot rules
9. `.github/agents/trustrail-engineer.agent.md`
10. `.github/agents/security-reviewer.agent.md`
11. `.github/agents/architect.agent.md`
12. `.github/prompts/implement-feature.prompt.md`
13. `.github/prompts/security-review.prompt.md`
14. `.github/prompts/test-feature.prompt.md`
15. `README.md`
16. `MASTER-BUILD-SEQUENCE.md`

---

## Recommended Stack

Backend:
- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy 2.x async
- PostgreSQL
- Alembic

Policy:
- OPA / Rego

Frontend:
- React
- TypeScript
- Vite
- Tailwind CSS

Quality:
- pytest
- HTTPX
- Ruff
- mypy
- GitHub Actions

Infrastructure:
- Docker
- Docker Compose

---

## How to Use This Pack

### 1. Create the repository

```bash
mkdir trustrail
cd trustrail
git init
```

Copy this pack into the repository root.

### 2. Open in VS Code

```bash
code .
```

Install/enable:
- GitHub Copilot;
- GitHub Copilot Chat;
- Python extension;
- Docker extension;
- recommended frontend extensions if desired.

### 3. Read the specifications

Before coding, review:
- `01-PRD.md`
- `02-ARCHITECTURE.md`
- `05-SECURITY.md`
- `MASTER-BUILD-SEQUENCE.md`

### 4. Use the custom architect

Ask the `TrustRail Architect` agent:

```text
Plan Milestone 1 from MASTER-BUILD-SEQUENCE.md.
Do not implement yet.
```

### 5. Use the engineer

After reviewing the plan:

```text
Implement Milestone 1 exactly as specified.
Do not proceed to Milestone 2.
```

### 6. Commit every milestone

Example:

```bash
git add .
git commit -m "chore: initialize TrustRail backend and local infrastructure"
```

### 7. Run the security reviewer regularly

After every authorization-sensitive milestone:

```text
Review the current implementation for authentication,
tenant isolation, fail-open behavior, and policy bypass.
Do not modify code.
```

---

## Golden Rules

- Never build the entire system with one prompt.
- Never let an LLM make the final authorization decision.
- Never store plaintext API keys.
- Never expose another tenant's resources.
- Never mutate historical authorization evidence.
- Never return ALLOW when a dependency is unavailable.
- Never weaken tests to make CI green.

---

## First Demo Goal

Create a simulated refund agent:

```text
$200 refund     -> ALLOW
$2,800 refund   -> ESCALATE
$18,500 refund  -> BLOCK
```

Then demonstrate:

1. valid Action Certificate verifies;
2. modified certificate fails;
3. audit chain verifies;
4. modified historical event breaks verification.

If all four work, TrustRail has proven its core primitive.
