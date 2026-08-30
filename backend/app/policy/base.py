from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class PolicyInput(BaseModel):
    """Input sent to the policy engine for a single evaluation."""

    # OPA data path, e.g. "trustrail/dev/ping/result".
    policy_path: str
    # Becomes the OPA {"input": ...} document.
    document: dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluation(BaseModel):
    """Structured policy result. Mirrors 06-DECISION-ENGINE §2.

    Strict: unknown fields rejected and the three decision booleans are required,
    so a partial or wrongly typed engine response fails validation (fail closed).
    """

    model_config = ConfigDict(extra="forbid")

    allow: bool
    requires_approval: bool
    hard_deny: bool
    reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluatorError(Exception):
    """Base error for policy evaluation failures. Callers must treat as fail-closed."""


class PolicyUnavailableError(PolicyEvaluatorError):
    """The policy engine could not be reached or did not respond successfully."""


class PolicyMalformedError(PolicyEvaluatorError):
    """The policy engine responded but the result was missing or not well-formed."""


class PolicyEvaluator(Protocol):
    async def evaluate(self, policy_input: PolicyInput) -> PolicyEvaluation: ...
