from __future__ import annotations

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

import brasileirao_data_lab.api.status_router as status_module

from brasileirao_data_lab.update_metadata import (
    UpdateMetadata,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def metadata() -> UpdateMetadata:
    """
    Metadata controlado para os testes.
    """

    return UpdateMetadata(
        season=2026,
        source="CBF",
        status="up_to_date",
        last_sync_at_utc="2026-08-20T12:11:52Z",
        total_matches=380,
        played_matches=225,
        future_matches=155,
        automation_enabled=True,
        checks_per_day=4,
    )


@pytest.fixture
def client(
    monkeypatch,
    metadata: UpdateMetadata,
) -> TestClient:
    """
    Cria uma API mínima contendo
    somente o router de status.
    """

    monkeypatch.setattr(
        status_module,
        "load_update_metadata",
        lambda: metadata,
    )

    app = FastAPI()

    app.include_router(
        status_module.router
    )

    return TestClient(
        app
    )


# =============================================================================
# Endpoint
# =============================================================================


def test_update_status(
    client: TestClient,
):
    response = client.get(
        "/api/status"
    )

    assert response.status_code == 200

    assert response.json() == {
        "season": 2026,
        "source": "CBF",
        "status": "up_to_date",
        "last_sync_at_utc": "2026-08-20T12:11:52Z",
        "total_matches": 380,
        "played_matches": 225,
        "future_matches": 155,
        "automation_enabled": True,
        "checks_per_day": 4,
    }


def test_update_status_response_contains_all_fields(
    client: TestClient,
):
    response = client.get(
        "/api/status"
    )

    data = response.json()

    expected_fields = {
        "season",
        "source",
        "status",
        "last_sync_at_utc",
        "total_matches",
        "played_matches",
        "future_matches",
        "automation_enabled",
        "checks_per_day",
    }

    assert set(
        data.keys()
    ) == expected_fields