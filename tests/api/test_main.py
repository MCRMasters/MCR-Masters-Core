from fastapi import status


async def test_health_check(client):
    client_instance, _ = client
    response = await client_instance.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "healthy"
