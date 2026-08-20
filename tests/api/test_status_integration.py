from __future__ import annotations

from fastapi.testclient import TestClient

import brasileirao_data_lab.api.app as api_module
import brasileirao_data_lab.api.status_router as status_module

from brasileirao_data_lab.update_metadata import (
    UpdateMetadata,
)


def test_status_endpoint_is_registered_in_main_api(
    monkeypatch,
):
    """
    Confirma que /api/status não funciona
    apenas no router isolado.

    Ele precisa estar registrado na aplicação
    FastAPI principal utilizada em produção.
    """

    metadata = UpdateMetadata(
        season=2026,
        source="CBF",
        status="up_to_date",
        last_sync_at_utc=(
            "2026-08-20T12:11:52Z"
        ),
        total_matches=380,
        played_matches=225,
        future_matches=155,
        automation_enabled=True,
        checks_per_day=4,
    )

    monkeypatch.setattr(
        status_module,
        "load_update_metadata",
        lambda: metadata,
    )

    client = TestClient(
        api_module.app
    )

    response = client.get(
        "/api/status"
    )

    assert response.status_code == 200

    assert response.json() == {
        "season": 2026,
        "source": "CBF",
        "status": "up_to_date",
        "last_sync_at_utc": (
            "2026-08-20T12:11:52Z"
        ),
        "total_matches": 380,
        "played_matches": 225,
        "future_matches": 155,
        "automation_enabled": True,
        "checks_per_day": 4,
    }


def test_status_endpoint_is_exposed_in_openapi():
    """
    Confirma que o endpoint também aparece
    na documentação Swagger/OpenAPI.
    """

    client = TestClient(
        api_module.app
    )

    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200

    paths = response.json()[
        "paths"
    ]

    assert (
        "/api/status"
        in paths
    )