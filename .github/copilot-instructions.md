# TrustRail Repository Instructions for GitHub Copilot

TrustRail is security-critical infrastructure for authorizing autonomous AI-agent actions.

## Product Contract

An AI agent requests permission to perform an action.

TrustRail evaluates:
1. authenticated organization;
2. agent identity and status;
3. delegated authority;
4. active policy;
5. contextual deterministic risk.

TrustRail returns exactly one decision:
- `ALLOW`
- `ESCALATE`
- `BLOCK`

Every decision must be auditable.

## Non-Negotiable Engineering Rules

- Security and correctness are more important than implementation speed.
- Fail closed.
- Never silently bypass authorization.
- Never use an LLM as the final authorization authority.
- Authorization logic must be deterministic and testable in v0.1.
- Never log API keys, passwords, signing private keys, or external tokens.
- Never store plaintext API keys.
- Validate all external input using Pydantic.
- Enforce strict organization/tenant isolation.
- Never trust organization IDs supplied by untrusted clients when tenant can be derived from credentials.
- Use type hints throughout Python.
- Use timezone-aware UTC timestamps.
- Keep business logic outside FastAPI route handlers.
- Keep database access inside repositories.
- Do not overwrite historical decisions, approvals, certificates, or audit events.
- Do not add infrastructure not required by the current milestone.

## Stack

Backend:
- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy 2.x async
- PostgreSQL
- Alembic

Policy:
- OPA
- Rego

Risk:
- deterministic Python rules

Certificates:
- Ed25519
- SHA-256
- canonical JSON

Frontend:
- React
- TypeScript
- Vite
- Tailwind CSS

Testing:
- pytest
- HTTPX
- Ruff
- mypy

Infrastructure:
- Docker
- Docker Compose
- GitHub Actions

## Layering

Use:

```text
backend/app/api
backend/app/core
backend/app/models
backend/app/schemas
backend/app/services
backend/app/repositories
backend/app/security
backend/app/policy
backend/app/risk
```

Rules:
- API routes handle HTTP concerns.
- Services orchestrate business behavior.
- Repositories own persistence.
- Security helpers live under `security`.
- OPA integration lives behind a policy adapter.
- Decision Engine performs no network/database I/O.

## Tests

Every authorization-sensitive feature requires tests.

Before considering a backend task complete, run:

```bash
ruff check .
mypy backend/app
pytest
```

Policy tasks:

```bash
opa fmt --fail policies
opa test policies
```

Frontend tasks:

```bash
npm run lint
npm run typecheck
npm run build
```

Never weaken, skip, or delete a failing security test merely to make CI pass.

## Authorization Rules

- invalid/disabled agent => never ALLOW;
- no applicable active policy => BLOCK;
- malformed policy result => BLOCK;
- OPA unavailable => never ALLOW;
- hard policy deny overrides risk;
- risk may tighten but never loosen policy;
- unresolved decision state => BLOCK.

## Audit

Audit events are append-only.
Use canonical JSON + SHA-256 hash chaining.
Protect organization-scoped sequencing against concurrent writes.

## Certificates

Sign canonical Action Certificate payloads with Ed25519.
Never commit a private signing key.
Do not expose sensitive raw action parameters in certificates by default.

## API Keys

Generate high-entropy secrets.
Return raw secret once.
Store only a verifier/hash plus non-secret prefix.
Support revocation and expiration.

## Change Discipline

Before implementing a feature:
1. inspect relevant existing code;
2. identify security implications;
3. identify schema/API changes;
4. implement the smallest correct solution;
5. add tests;
6. run quality gates;
7. summarize changed files and risks.

Do not refactor unrelated code during a scoped feature.
