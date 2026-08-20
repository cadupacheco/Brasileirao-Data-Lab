from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from brasileirao_data_lab.update_metadata import (
    load_update_metadata,
)


class UpdateStatusResponse(
    BaseModel
):
    """
    Estado público da atualização automática
    dos dados do Brasileirão.
    """

    season: int
    source: str
    status: str

    last_sync_at_utc: str

    total_matches: int
    played_matches: int
    future_matches: int

    automation_enabled: bool
    checks_per_day: int


router = APIRouter(
    prefix="/api",
    tags=[
        "System",
    ],
)


@router.get(
    "/status",
    response_model=UpdateStatusResponse,
)
def update_status(
) -> UpdateStatusResponse:
    """
    Retorna informações sobre a versão
    atualmente publicada dos dados.
    """

    metadata = (
        load_update_metadata()
    )

    return UpdateStatusResponse(
        season=metadata.season,
        source=metadata.source,
        status=metadata.status,
        last_sync_at_utc=(
            metadata.last_sync_at_utc
        ),
        total_matches=(
            metadata.total_matches
        ),
        played_matches=(
            metadata.played_matches
        ),
        future_matches=(
            metadata.future_matches
        ),
        automation_enabled=(
            metadata.automation_enabled
        ),
        checks_per_day=(
            metadata.checks_per_day
        ),
    )