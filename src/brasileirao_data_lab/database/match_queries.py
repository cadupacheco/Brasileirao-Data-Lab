from __future__ import annotations

from typing import Literal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from brasileirao_data_lab.database.models import Match
from brasileirao_data_lab.database.repository import (
    create_match_select,
    execute_match_query,
)


MatchStatus = Literal[
    "all",
    "played",
    "upcoming",
]


def get_matches_from_database(
    session: Session,
    season: int,
    round_number: int | None = None,
    team_id: int | None = None,
    status: MatchStatus = "all",
) -> list[dict]:
    """
    Retorna partidas da temporada com
    filtros opcionais por:

    - rodada
    - clube
    - status

    Status disponíveis:

    - all
    - played
    - upcoming
    """

    statement = (
        create_match_select()
        .where(
            Match.season
            == season
        )
    )

    if round_number is not None:
        statement = statement.where(
            Match.round
            == round_number
        )

    if team_id is not None:
        statement = statement.where(
            or_(
                Match.home_team_id
                == team_id,
                Match.away_team_id
                == team_id,
            )
        )

    if status == "played":
        statement = statement.where(
            Match.home_goals.is_not(
                None
            ),
            Match.away_goals.is_not(
                None
            ),
        )

    elif status == "upcoming":
        statement = statement.where(
            Match.home_goals.is_(
                None
            ),
            Match.away_goals.is_(
                None
            ),
        )

    statement = statement.order_by(
        Match.round,
        Match.date,
        Match.time,
        Match.match_number,
        Match.match_id,
    )

    return execute_match_query(
        session,
        statement,
    )