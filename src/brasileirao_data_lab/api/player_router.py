from __future__ import annotations

from datetime import date

import pandas as pd

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)
from pydantic import BaseModel

from brasileirao_data_lab.analytics.comparison import (
    compare_teams,
)
from brasileirao_data_lab.database.analytics_bridge import (
    load_matches_for_analytics,
)
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
# Responses - jogadores
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
# Responses - comparação
# =============================================================================


class ClubComparisonTeamResponse(
    BaseModel
):
    team_id: int
    team: str

    position: int

    matches: int
    wins: int
    draws: int
    losses: int

    points: int

    goals_for: int
    goals_against: int
    goal_difference: int

    performance_pct: float

    home_matches: int
    home_wins: int
    home_draws: int
    home_losses: int
    home_points: int
    home_performance_pct: float

    away_matches: int
    away_wins: int
    away_draws: int
    away_losses: int
    away_points: int
    away_performance_pct: float

    recent_matches: int
    recent_wins: int
    recent_draws: int
    recent_losses: int
    recent_points: int

    recent_goals_for: int
    recent_goals_against: int
    recent_goal_difference: int

    recent_performance_pct: float
    recent_form: str


class HeadToHeadGameResponse(
    BaseModel
):
    match_id: int | None
    round: int | None

    date: date | None

    home_team: str
    away_team: str

    home_goals: int
    away_goals: int


class HeadToHeadResponse(
    BaseModel
):
    matches: int

    team_a_wins: int
    team_b_wins: int
    draws: int

    team_a_goals: int
    team_b_goals: int

    games: list[
        HeadToHeadGameResponse
    ]


class ClubComparisonResponse(
    BaseModel
):
    recent_n: int

    team_a: (
        ClubComparisonTeamResponse
    )

    team_b: (
        ClubComparisonTeamResponse
    )

    metric_winners: dict[
        str,
        int | None,
    ]

    team_a_advantages: int
    team_b_advantages: int

    overall_advantage: int | None

    head_to_head: (
        HeadToHeadResponse
    )


# =============================================================================
# Helpers - comparação
# =============================================================================


def load_comparison_matches(
) -> pd.DataFrame:
    """
    Carrega as partidas do SQLite
    no formato utilizado pelo Analytics.
    """

    with SessionLocal() as session:
        return load_matches_for_analytics(
            session
        )


def build_team_comparison_response(
    team: dict,
) -> ClubComparisonTeamResponse:
    """
    Converte o perfil calculado
    pelo Analytics para o contrato
    público da API.
    """

    return (
        ClubComparisonTeamResponse(
            team_id=int(
                team[
                    "team_id"
                ]
            ),
            team=str(
                team[
                    "team"
                ]
            ),
            position=int(
                team[
                    "position"
                ]
            ),
            matches=int(
                team[
                    "matches"
                ]
            ),
            wins=int(
                team[
                    "wins"
                ]
            ),
            draws=int(
                team[
                    "draws"
                ]
            ),
            losses=int(
                team[
                    "losses"
                ]
            ),
            points=int(
                team[
                    "points"
                ]
            ),
            goals_for=int(
                team[
                    "goals_for"
                ]
            ),
            goals_against=int(
                team[
                    "goals_against"
                ]
            ),
            goal_difference=int(
                team[
                    "goal_difference"
                ]
            ),
            performance_pct=float(
                team[
                    "performance_pct"
                ]
            ),
            home_matches=int(
                team[
                    "home_matches"
                ]
            ),
            home_wins=int(
                team[
                    "home_wins"
                ]
            ),
            home_draws=int(
                team[
                    "home_draws"
                ]
            ),
            home_losses=int(
                team[
                    "home_losses"
                ]
            ),
            home_points=int(
                team[
                    "home_points"
                ]
            ),
            home_performance_pct=float(
                team[
                    "home_performance_pct"
                ]
            ),
            away_matches=int(
                team[
                    "away_matches"
                ]
            ),
            away_wins=int(
                team[
                    "away_wins"
                ]
            ),
            away_draws=int(
                team[
                    "away_draws"
                ]
            ),
            away_losses=int(
                team[
                    "away_losses"
                ]
            ),
            away_points=int(
                team[
                    "away_points"
                ]
            ),
            away_performance_pct=float(
                team[
                    "away_performance_pct"
                ]
            ),
            recent_matches=int(
                team[
                    "recent_matches"
                ]
            ),
            recent_wins=int(
                team[
                    "recent_wins"
                ]
            ),
            recent_draws=int(
                team[
                    "recent_draws"
                ]
            ),
            recent_losses=int(
                team[
                    "recent_losses"
                ]
            ),
            recent_points=int(
                team[
                    "recent_points"
                ]
            ),
            recent_goals_for=int(
                team[
                    "recent_goals_for"
                ]
            ),
            recent_goals_against=int(
                team[
                    "recent_goals_against"
                ]
            ),
            recent_goal_difference=int(
                team[
                    "recent_goal_difference"
                ]
            ),
            recent_performance_pct=float(
                team[
                    "recent_performance_pct"
                ]
            ),
            recent_form=str(
                team[
                    "recent_form"
                ]
            ),
        )
    )


# =============================================================================
# Endpoint - comparação
# =============================================================================


@router.get(
    "/compare",
    response_model=(
        ClubComparisonResponse
    ),
    tags=[
        "Clubs",
    ],
)
def compare_clubs(
    team_a: int = Query(
        ...,
        gt=0,
        description=(
            "ID do primeiro clube."
        ),
    ),
    team_b: int = Query(
        ...,
        gt=0,
        description=(
            "ID do segundo clube."
        ),
    ),
    recent_n: int = Query(
        default=5,
        ge=1,
        le=20,
        description=(
            "Quantidade de jogos "
            "recentes considerada."
        ),
    ),
) -> ClubComparisonResponse:
    """
    Compara dois clubes do Brasileirão.

    Inclui:

    - classificação atual;
    - campanha;
    - gols;
    - aproveitamento;
    - desempenho em casa;
    - desempenho fora;
    - forma recente;
    - confronto direto;
    - vantagem por métrica.
    """

    if team_a == team_b:
        raise HTTPException(
            status_code=400,
            detail=(
                "Os clubes da comparação "
                "devem ser diferentes."
            ),
        )

    matches = (
        load_comparison_matches()
    )

    try:
        result = compare_teams(
            matches=matches,
            team_a_id=team_a,
            team_b_id=team_b,
            recent_n=recent_n,
        )

    except ValueError as error:
        message = str(
            error
        )

        status_code = (
            404
            if (
                "não encontrado"
                in message.casefold()
            )
            else 400
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from error

    team_a_data = result[
        "team_a"
    ]

    team_b_data = result[
        "team_b"
    ]

    advantages = result[
        "advantages"
    ]

    h2h = result[
        "head_to_head"
    ]

    return ClubComparisonResponse(
        recent_n=recent_n,
        team_a=(
            build_team_comparison_response(
                team_a_data
            )
        ),
        team_b=(
            build_team_comparison_response(
                team_b_data
            )
        ),
        metric_winners={
            str(
                metric
            ): (
                int(
                    winner
                )
                if winner
                is not None
                else None
            )
            for metric, winner
            in result[
                "metric_winners"
            ].items()
        },
        team_a_advantages=int(
            advantages[
                team_a
            ]
        ),
        team_b_advantages=int(
            advantages[
                team_b
            ]
        ),
        overall_advantage=(
            int(
                result[
                    "overall_advantage"
                ]
            )
            if result[
                "overall_advantage"
            ]
            is not None
            else None
        ),
        head_to_head=(
            HeadToHeadResponse(
                matches=int(
                    h2h[
                        "matches"
                    ]
                ),
                team_a_wins=int(
                    h2h[
                        "team_a_wins"
                    ]
                ),
                team_b_wins=int(
                    h2h[
                        "team_b_wins"
                    ]
                ),
                draws=int(
                    h2h[
                        "draws"
                    ]
                ),
                team_a_goals=int(
                    h2h[
                        "team_a_goals"
                    ]
                ),
                team_b_goals=int(
                    h2h[
                        "team_b_goals"
                    ]
                ),
                games=[
                    HeadToHeadGameResponse(
                        match_id=(
                            int(
                                game[
                                    "match_id"
                                ]
                            )
                            if game[
                                "match_id"
                            ]
                            is not None
                            else None
                        ),
                        round=(
                            int(
                                game[
                                    "round"
                                ]
                            )
                            if game[
                                "round"
                            ]
                            is not None
                            else None
                        ),
                        date=(
                            game[
                                "date"
                            ]
                        ),
                        home_team=str(
                            game[
                                "home_team"
                            ]
                        ),
                        away_team=str(
                            game[
                                "away_team"
                            ]
                        ),
                        home_goals=int(
                            game[
                                "home_goals"
                            ]
                        ),
                        away_goals=int(
                            game[
                                "away_goals"
                            ]
                        ),
                    )
                    for game
                    in h2h[
                        "games"
                    ]
                ],
            )
        ),
    )


# =============================================================================
# Endpoint - jogadores
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