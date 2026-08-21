from __future__ import annotations

from datetime import date

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)
from pydantic import BaseModel

from brasileirao_data_lab.database.player_queries import (
    get_team_or_none,
    get_team_players_with_age,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
)
from brasileirao_data_lab.scrapers.cbf_players import (
    CBF_CHAMPIONSHIP_ID,
    CBF_SEASON,
)


# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/clubs",
    tags=[
        "Clubs",
        "Players",
    ],
)


# =============================================================================
# Responses
# =============================================================================


class ClubPlayerResponse(BaseModel):
    season: int

    competition_id: int
    competition_name: str
    category: str

    team_id: int
    team: str

    player_id: int
    full_name: str
    nickname: str | None

    birth_date: date | None
    age: int | None

    profile_url: str | None

    current_club_id: int | None
    current_club_name: str | None
    current_club_state: str | None
    current_club_badge_url: str | None

    is_current_club: bool

    matches: int
    goals: int
    yellow_cards: int
    red_cards: int


# =============================================================================
# Endpoint
# =============================================================================


@router.get(
    "/{team_id}/players",
    response_model=list[
        ClubPlayerResponse
    ],
)
def get_club_players(
    team_id: int,
    season: int = Query(
        default=CBF_SEASON,
        ge=1900,
        le=2100,
        description=(
            "Temporada das estatísticas."
        ),
    ),
    competition_id: int = Query(
        default=CBF_CHAMPIONSHIP_ID,
        gt=0,
        description=(
            "ID da edição da competição "
            "utilizado pela CBF."
        ),
    ),
) -> list[ClubPlayerResponse]:
    """
    Retorna jogadores associados
    ao clube na competição.

    As estatísticas retornadas são
    específicas daquele clube.
    """

    with SessionLocal() as session:
        team = get_team_or_none(
            session=session,
            team_id=team_id,
        )

        if team is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Clube não encontrado."
                ),
            )

        players = (
            get_team_players_with_age(
                session=session,
                team_id=team_id,
                season=season,
                competition_id=competition_id,
            )
        )

    return [
        ClubPlayerResponse(
            season=int(
                player[
                    "season"
                ]
            ),
            competition_id=int(
                player[
                    "competition_id"
                ]
            ),
            competition_name=str(
                player[
                    "competition_name"
                ]
            ),
            category=str(
                player[
                    "category"
                ]
            ),
            team_id=int(
                player[
                    "team_id"
                ]
            ),
            team=str(
                player[
                    "team"
                ]
            ),
            player_id=int(
                player[
                    "player_id"
                ]
            ),
            full_name=str(
                player[
                    "full_name"
                ]
            ),
            nickname=(
                str(
                    player[
                        "nickname"
                    ]
                )
                if player[
                    "nickname"
                ]
                is not None
                else None
            ),
            birth_date=player[
                "birth_date"
            ],
            age=(
                int(
                    player[
                        "age"
                    ]
                )
                if player[
                    "age"
                ]
                is not None
                else None
            ),
            profile_url=(
                str(
                    player[
                        "profile_url"
                    ]
                )
                if player[
                    "profile_url"
                ]
                is not None
                else None
            ),
            current_club_id=(
                int(
                    player[
                        "current_club_id"
                    ]
                )
                if player[
                    "current_club_id"
                ]
                is not None
                else None
            ),
            current_club_name=(
                str(
                    player[
                        "current_club_name"
                    ]
                )
                if player[
                    "current_club_name"
                ]
                is not None
                else None
            ),
            current_club_state=(
                str(
                    player[
                        "current_club_state"
                    ]
                )
                if player[
                    "current_club_state"
                ]
                is not None
                else None
            ),
            current_club_badge_url=(
                str(
                    player[
                        "current_club_badge_url"
                    ]
                )
                if player[
                    "current_club_badge_url"
                ]
                is not None
                else None
            ),
            is_current_club=bool(
                player[
                    "is_current_club"
                ]
            ),
            matches=int(
                player[
                    "matches"
                ]
            ),
            goals=int(
                player[
                    "goals"
                ]
            ),
            yellow_cards=int(
                player[
                    "yellow_cards"
                ]
            ),
            red_cards=int(
                player[
                    "red_cards"
                ]
            ),
        )
        for player in players
    ]