import os

import httpx
import pytest

from app.policy.base import (
    PolicyEvaluation,
    PolicyInput,
    PolicyMalformedError,
    PolicyUnavailableError,
)
from app.policy.opa_client import OpaPolicyEvaluator, get_policy_evaluator

_PING = PolicyInput(policy_path="trustrail/dev/ping/result")

_WELL_FORMED = {
    "result": {
        "allow": True,
        "requires_approval": False,
        "hard_deny": False,
        "reasons": [],
        "metadata": {"policy": "dev-ping"},
    }
}


def _evaluator(handler: object, base_url: str = "http://opa.test") -> OpaPolicyEvaluator:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    client = httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(2.0))
    return OpaPolicyEvaluator(client, base_url)


async def test_well_formed_response_parses() -> None:
    evaluator = _evaluator(lambda request: httpx.Response(200, json=_WELL_FORMED))
    result = await evaluator.evaluate(_PING)
    assert isinstance(result, PolicyEvaluation)
    assert result.allow is True
    assert result.hard_deny is False


async def test_missing_result_fails_closed() -> None:
    evaluator = _evaluator(lambda request: httpx.Response(200, json={"other": 1}))
    with pytest.raises(PolicyMalformedError):
        await evaluator.evaluate(_PING)


async def test_wrong_types_fail_closed() -> None:
    bad = {"result": {"requires_approval": False, "hard_deny": False}}  # missing allow
    evaluator = _evaluator(lambda request: httpx.Response(200, json=bad))
    with pytest.raises(PolicyMalformedError):
        await evaluator.evaluate(_PING)


async def test_non_json_body_fails_closed() -> None:
    evaluator = _evaluator(lambda request: httpx.Response(200, content=b"not json"))
    with pytest.raises(PolicyMalformedError):
        await evaluator.evaluate(_PING)


async def test_non_200_fails_closed() -> None:
    evaluator = _evaluator(lambda request: httpx.Response(500, text="boom"))
    with pytest.raises(PolicyUnavailableError):
        await evaluator.evaluate(_PING)


async def test_timeout_fails_closed() -> None:
    def _raise(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout", request=request)

    evaluator = _evaluator(_raise)
    with pytest.raises(PolicyUnavailableError):
        await evaluator.evaluate(_PING)


async def test_connection_error_fails_closed() -> None:
    def _raise(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    evaluator = _evaluator(_raise)
    with pytest.raises(PolicyUnavailableError):
        await evaluator.evaluate(_PING)


async def test_unconfigured_url_fails_closed() -> None:
    evaluator = _evaluator(lambda request: httpx.Response(200, json=_WELL_FORMED), base_url=None)
    with pytest.raises(PolicyUnavailableError):
        await evaluator.evaluate(_PING)


async def test_unreachable_opa_real_client_fails_closed() -> None:
    # A real client pointed at a closed port must fail closed, never ALLOW.
    client = httpx.AsyncClient(timeout=httpx.Timeout(1.0))
    evaluator = OpaPolicyEvaluator(client, "http://127.0.0.1:1")
    try:
        with pytest.raises(PolicyUnavailableError):
            await evaluator.evaluate(_PING)
    finally:
        await client.aclose()


@pytest.mark.opa
async def test_live_opa_returns_structured_result() -> None:
    if not os.environ.get("OPA_URL"):
        pytest.skip("OPA_URL not set; skipping live OPA integration test.")
    evaluator = get_policy_evaluator()
    result = await evaluator.evaluate(_PING)
    assert result.allow is True
    assert result.requires_approval is False
    assert result.hard_deny is False
    assert result.metadata.get("policy") == "dev-ping"


@pytest.mark.opa
async def test_live_opa_health_check() -> None:
    if not os.environ.get("OPA_URL"):
        pytest.skip("OPA_URL not set; skipping live OPA health check.")
    assert await get_policy_evaluator().health_check() is True
