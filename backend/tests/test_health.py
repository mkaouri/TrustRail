from httpx import AsyncClient

from app.core.request_id import REQUEST_ID_HEADER


async def test_health_returns_expected_body(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "trustrail",
        "version": "0.1.0",
    }


async def test_health_sets_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert REQUEST_ID_HEADER in response.headers
    assert response.headers[REQUEST_ID_HEADER].startswith("req_")


async def test_health_echoes_inbound_request_id(client: AsyncClient) -> None:
    response = await client.get("/health", headers={REQUEST_ID_HEADER: "req_fixed123"})

    assert response.headers[REQUEST_ID_HEADER] == "req_fixed123"
