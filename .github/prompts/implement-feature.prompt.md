---
description: Implement one bounded TrustRail feature safely
agent: TrustRail Engineer
---

Implement the requested TrustRail feature.

Before editing:
1. inspect all relevant existing code;
2. inspect applicable specifications;
3. identify tenant-isolation impact;
4. identify fail-closed behavior;
5. identify schema/API impact;
6. list required tests.

Implementation rules:
- implement only the requested feature;
- keep routes thin;
- place persistence in repositories;
- place orchestration in services;
- use Pydantic validation;
- use async SQLAlchemy;
- add explicit reason codes;
- preserve immutable history;
- do not expose secrets;
- do not introduce an LLM into authorization.

Testing:
- add success tests;
- add failure tests;
- add cross-tenant tests when tenant-owned data is involved;
- add dependency-failure tests when external components are involved.

After editing run as applicable:

```bash
ruff check .
mypy backend/app
pytest
opa fmt --fail policies
opa test policies
npm run lint
npm run typecheck
npm run build
```

If any check fails, fix the actual defect rather than weakening tests.

Finish with:
- files changed;
- behavior implemented;
- tests added;
- commands run;
- remaining risks.
