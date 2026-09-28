from django.urls import reverse

from accounts.models import User


def test_register_creates_owner(client, db):
    resp = client.post(
        reverse("register"),
        {"username": "newuser", "email": "new@test.dev", "password": "supersecret123"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["user"]["role"] == User.OWNER  # first account becomes owner
    assert "access" in resp.data and "refresh" in resp.data


def test_register_duplicate_email(client, db):
    client.post(
        reverse("register"),
        {"username": "newuser", "email": "new@test.dev", "password": "supersecret123"},
        format="json",
    )
    resp = client.post(
        reverse("register"),
        {"username": "newuser2", "email": "new@test.dev", "password": "supersecret123"},
        format="json",
    )
    assert resp.status_code == 400
    assert "An account with this email already exists." in str(resp.data)


def test_login_returns_jwt(client, db):
    User.objects.create_user(username="admin", email="admin@test.dev", password="GHOST CHANGE", role=User.OWNER)
    resp = client.post(
        reverse("token_obtain_pair"),
        {"username": "admin", "password": "GHOST CHANGE"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["access"]


def test_login_brute_force_throttling(client, db):
    User.objects.create_user(username="admin", email="admin@test.dev", password="GHOST CHANGE", role=User.OWNER)
    for _ in range(5):
        client.post(
            reverse("token_obtain_pair"),
            {"username": "admin", "password": "wrong_password"},
            format="json",
        )
    resp = client.post(
        reverse("token_obtain_pair"),
        {"username": "admin", "password": "wrong_password"},
        format="json",
    )
    assert resp.status_code == 429
    assert "Expected available in" in str(resp.data)


def test_me_requires_auth(client, db):
    assert client.get(reverse("me")).status_code == 401


def test_me_returns_profile(auth_client, owner):
    resp = auth_client.get(reverse("me"))
    assert resp.status_code == 200
    assert resp.data["username"] == owner.username
