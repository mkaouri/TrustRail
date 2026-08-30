import httpx
from pydantic import ValidationError

from app.core.config import get_settings
from app.policy.base import (
    PolicyEvaluation,
    PolicyInput,
    PolicyMalformedError,
    PolicyUnavailableError,
)

_client: httpx.AsyncClient | None = None


def get_opa_client() -> httpx.AsyncClient:
    """Return the process-wide async HTTP client with the configured strict timeout."""

    global _client
    if _client is None:
        settings = get_settings()
        _client = httpx.AsyncClient(timeout=httpx.Timeout(settings.opa_timeout_seconds))
    return _client


async def dispose_opa_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
    _client = None


class OpaPolicyEvaluator:
    """PolicyEvaluator backed by an OPA server. Every failure path fails closed."""

    def __init__(self, client: httpx.AsyncClient, base_url: str | None) -> None:
        self._client = client
        self._base_url = base_url

    async def evaluate(self, policy_input: PolicyInput) -> PolicyEvaluation:
        if not self._base_url:
            raise PolicyUnavailableError("OPA_URL is not configured.")

        url = f"{self._base_url.rstrip('/')}/v1/data/{policy_input.policy_path.strip('/')}"
        try:
            try:
                response = await self._client.post(url, json={"input": policy_input.document})
            except httpx.TimeoutException as exc:
                raise PolicyUnavailableError("OPA request timed out.") from exc
            except httpx.HTTPError as exc:
                raise PolicyUnavailableError("OPA request failed.") from exc

            if response.status_code != 200:
                raise PolicyUnavailableError(f"OPA returned status {response.status_code}.")

            try:
                body = response.json()
            except ValueError as exc:
                raise PolicyMalformedError("OPA returned a non-JSON body.") from exc

            if not isinstance(body, dict) or "result" not in body:
                raise PolicyMalformedError("OPA response missing 'result'.")

            try:
                return PolicyEvaluation.model_validate(body["result"])
            except ValidationError as exc:
                raise PolicyMalformedError("OPA result failed structural validation.") from exc
        except PolicyUnavailableError:
            raise
        except PolicyMalformedError:
            raise
        except Exception as exc:
            # Any unexpected error must fail closed, never permit ALLOW.
            raise PolicyUnavailableError("Unexpected error during OPA evaluation.") from exc

    async def health_check(self) -> bool:
        """Return True only if OPA is reachable and healthy; never raises."""

        if not self._base_url:
            return False
        url = f"{self._base_url.rstrip('/')}/health"
        try:
            response = await self._client.get(url)
        except httpx.HTTPError:
            return False
        return response.status_code == 200


def get_policy_evaluator() -> OpaPolicyEvaluator:
    settings = get_settings()
    return OpaPolicyEvaluator(get_opa_client(), settings.opa_url)
