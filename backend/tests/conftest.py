"""Shared pytest fixtures."""
import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from github.models import Repository, Commit


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
    """Seed the minimal dataset for tests."""
    from intelligence.models import IntegrationConnection

    # Ensure github integration is configured so GitHub skills pass the integration check.
    owner.github_username = "suragdev"
    owner.save(update_fields=["github_username"])
    
    IntegrationConnection.objects.create(
        owner=owner,
        platform="github",
        status="connected",
        connected_account="suragdev"
    )

    r = Repository.objects.create(
        owner=owner,
        name="legacy-dashboard",
        full_name="suragdev/legacy-dashboard",
        status="active",
        language="TypeScript",
        stars=0,
        forks=0,
        last_commit_at=timezone.now() - timedelta(days=60),
    )
    Repository.objects.create(
        owner=owner,
        name="active-repo",
        full_name="suragdev/active-repo",
        status="active",
        language="Python",
        last_commit_at=timezone.now(),
    )
    Repository.objects.create(owner=owner, name="repo3", full_name="suragdev/repo3", last_commit_at=timezone.now())
    Repository.objects.create(owner=owner, name="repo4", full_name="suragdev/repo4", last_commit_at=timezone.now())
    
    Commit.objects.create(
        owner=owner,
        repository=r,
        sha="abc1234",
        message="init",
        author="surag",
        date=timezone.now() - timedelta(days=1),
        additions=1000,
        deletions=10
    )
    for i in range(5):
        Commit.objects.create(
            owner=owner,
            repository=r,
            sha=f"commit{i}",
            message=f"msg {i}",
            author="surag",
            date=timezone.now() - timedelta(days=i),
            additions=500,
            deletions=10
        )

    from github.services import update_daily_metrics
    update_daily_metrics(owner)

    return owner
