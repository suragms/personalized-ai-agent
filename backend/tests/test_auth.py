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


def test_login_returns_jwt(client, db):
    User.objects.create_user(username="demo", email="demo@test.dev", password="demo12345", role=User.OWNER)
    resp = client.post(
        reverse("token_obtain_pair"),
        {"username": "demo", "password": "demo12345"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["access"]


def test_me_requires_auth(client, db):
    assert client.get(reverse("me")).status_code == 401


def test_me_returns_profile(auth_client, owner):
    resp = auth_client.get(reverse("me"))
    assert resp.status_code == 200
    assert resp.data["username"] == owner.username
