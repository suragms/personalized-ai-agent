"""Shared pytest fixtures."""
import pytest
from rest_framework.test import APIClient

from accounts.models import User


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        username="owner", email="owner@test.dev", password="ownerpass123", role=User.OWNER
    )


@pytest.fixture
def viewer(db):
    return User.objects.create_user(
        username="viewer", email="viewer@test.dev", password="viewerpass123", role=User.VIEWER
    )


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(owner):
    client = APIClient()
    client.force_authenticate(user=owner)
    return client


@pytest.fixture
def seeded(owner):
    """Seed the full demo dataset for the given owner."""
    from seeds.demo import seed_demo

    return seed_demo(owner)
