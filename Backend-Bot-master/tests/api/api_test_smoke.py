import importlib
from types import SimpleNamespace


def test_health_endpoint_is_public_and_alive(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_route_inventory_contains_current_critical_http_endpoints(app_instance):
    routes = {
        (method, route.path)
        for route in app_instance.routes
        for method in getattr(route, "methods", set())
        if route.path.startswith("/api/v1")
    }

    assert ("POST", "/api/v1/auth/send") in routes
    assert ("POST", "/api/v1/auth/verify") in routes
    assert ("POST", "/api/v1/auth/logout") in routes
    assert ("POST", "/api/v1/commissions/payments/{id}/payment-link") in routes
    assert ("GET", "/api/v1/ride-requests/ride/{id}") in routes
    assert ("GET", "/api/v1/documents/public/policy/{key:path}") in routes
    assert ("POST", "/api/v1/webhooks/tochka") in routes

    assert ("POST", "/api/v1/auth/login") not in routes
    assert ("POST", "/api/v1/auth/register") not in routes


def test_auth_send_smoke(client, monkeypatch):
    auth_module = importlib.import_module("app.backend.routers.auth")

    async def fake_login_or_register(session, phone, code_role=None):
        return SimpleNamespace(id=1, phone=phone)

    async def fake_send_otp(self, request, user):
        return {
            "id": 1,
            "user_id": user.id,
            "phone": user.phone,
            "code": "000000",
            "status": "sent",
            "attempts": 0,
            "expires_at": "2030-01-01T00:00:00Z",
            "next_sending_at": "2030-01-01T00:01:00Z",
            "created_at": "2030-01-01T00:00:00Z",
        }

    monkeypatch.setattr(auth_module.auth_crud, "login_or_register", fake_login_or_register)
    monkeypatch.setattr(auth_module.AuthRouter, "send_otp", fake_send_otp)

    response = client.post(
        "/api/v1/auth/send",
        json={"phone": "+79990000000", "code_role": "user"},
    )

    assert response.status_code == 200
    assert response.json()["phone"] == "79990000000"
    assert response.json()["code"] == "000000"


# def test_users_me_smoke_with_dependency_override(client, app_instance):
#     get_current_user = importlib.import_module("app.backend.deps.get_current_user").get_current_user

#     async def fake_get_current_user():
#         return SimpleNamespace(
#             id=1,
#             created_at=None,
#             updated_at=None,
#             last_active_at=None,
#             first_name="Иван",
#             last_name="Иванов",
#             middle_name=None,
#             phone="79990000000",
#             email=None,
#             city="Moscow",
#             photo_url=None,
#             is_active=True,
#             status="active",
#             role_id=1,
#             role=SimpleNamespace(code="user"),
#             driver_profile=None,
#         )

#     app_instance.dependency_overrides[get_current_user] = fake_get_current_user

#     response = client.get("/api/v1/users/me")

#     assert response.status_code == 200
#     assert response.json()["id"] == 1
#     assert response.json()["role_name"] == "user"
#     assert response.json()["is_active_ride"] is False


def test_public_policy_documents_are_available_for_allowed_keys(client, monkeypatch):
    documents_module = importlib.import_module("app.backend.routers.documents")

    async def fake_get_by_key(key, bucket=None):
        return b"%PDF-1.4\\n% smoke test pdf\\n"

    monkeypatch.setattr(documents_module.document_crud, "get_by_key", fake_get_by_key)

    for policy_key in (
        "privacy-policy",
        "confidentiality-policy",
        "terms-of-service",
        "public-offer",
    ):
        response = client.get(f"/api/v1/documents/public/policy/{policy_key}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF-1.4")

    invalid_response = client.get("/api/v1/documents/public/policy/not-allowed")
    assert invalid_response.status_code == 404
