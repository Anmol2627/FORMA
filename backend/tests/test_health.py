def test_health_check(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_readiness_check(client):
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
