from __future__ import annotations

from typing import Annotated

import pandas as pd
from fastapi import (
    FastAPI,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from brasileirao_data_lab.analytics.championship import (
    get_championship_summary,
    get_recent_form_table,
    get_team_stats,
)
from brasileirao_data_lab.analytics.evolution import (
    get_latest_played_round,
)
from brasileirao_data_lab.database.analytics_bridge import (
    load_matches_for_analytics,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
)


# =============================================================================
# Schemas
# =============================================================================


class HealthResponse(BaseModel):
    status: str
    version: str


class LeaderResponse(BaseModel):
    team_id: int
    team: str
    position: int
    points: int


class ChampionshipSummaryResponse(BaseModel):
    season: int
    total_matches: int
    played_matches: int
    future_matches: int
    total_goals: int
    average_goals_per_match: float
    home_wins: int
    draws: int
    away_wins: int
    latest_played_round: int | None
    leader: LeaderResponse | None


class StandingResponse(BaseModel):
    position: int
    team_id: int
    team: str
    matches: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    performance_pct: float


class RecentFormResponse(BaseModel):
    position: int
    team_id: int
    team: str
    matches: int
    wins: int
    draws: int
    losses: int
    points: int
    goals_for: int
    goals_against: int
    goal_difference: int
    performance_pct: float
    form: str


# =============================================================================
# Aplicação
# =============================================================================


app = FastAPI(
    title="Brasileirão Data Lab API",
    description=(
        "API REST para acesso aos dados e Analytics "
        "do Campeonato Brasileiro Série A."
    ),
    version="0.4.0",
)


# =============================================================================
# CORS
# =============================================================================


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Carregamento
# =============================================================================


def load_api_matches() -> pd.DataFrame:
    """
    Carrega as partidas utilizadas pela API.

    O SQLite é a fonte oficial de leitura
    da V0.4.
    """

    with SessionLocal() as session:

        return load_matches_for_analytics(
            session
        )


def get_matches_season(
    matches: pd.DataFrame,
) -> int:
    """Retorna a temporada mais recente do DataFrame."""

    seasons = (
        matches[
            "season"
        ]
        .dropna()
    )

    if seasons.empty:

        raise ValueError(
            "Nenhuma temporada encontrada."
        )

    return int(
        seasons.max()
    )


# =============================================================================
# Conversores
# =============================================================================


def build_leader(
    standings: pd.DataFrame,
) -> LeaderResponse | None:
    """Monta o líder atual do campeonato."""

    if standings.empty:

        return None

    leader = standings.iloc[
        0
    ]

    return LeaderResponse(
        team_id=int(
            leader[
                "team_id"
            ]
        ),
        team=str(
            leader[
                "team"
            ]
        ),
        position=int(
            leader[
                "calculated_position"
            ]
        ),
        points=int(
            leader[
                "points"
            ]
        ),
    )


def build_standings_response(
    standings: pd.DataFrame,
) -> list[StandingResponse]:
    """Converte a classificação para o schema da API."""

    result = []

    for _, team in standings.iterrows():

        result.append(
            StandingResponse(
                position=int(
                    team[
                        "calculated_position"
                    ]
                ),
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
                points=int(
                    team[
                        "points"
                    ]
                ),
                performance_pct=float(
                    team[
                        "performance_pct"
                    ]
                ),
            )
        )

    return result


def build_recent_form_response(
    recent_form: pd.DataFrame,
) -> list[RecentFormResponse]:
    """Converte a forma recente para o schema da API."""

    result = []

    for _, team in recent_form.iterrows():

        result.append(
            RecentFormResponse(
                position=int(
                    team[
                        "recent_position"
                    ]
                ),
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
                matches=int(
                    team[
                        "recent_matches"
                    ]
                ),
                wins=int(
                    team[
                        "recent_wins"
                    ]
                ),
                draws=int(
                    team[
                        "recent_draws"
                    ]
                ),
                losses=int(
                    team[
                        "recent_losses"
                    ]
                ),
                points=int(
                    team[
                        "recent_points"
                    ]
                ),
                goals_for=int(
                    team[
                        "recent_goals_for"
                    ]
                ),
                goals_against=int(
                    team[
                        "recent_goals_against"
                    ]
                ),
                goal_difference=int(
                    team[
                        "recent_goal_difference"
                    ]
                ),
                performance_pct=float(
                    team[
                        "recent_performance_pct"
                    ]
                ),
                form=str(
                    team[
                        "recent_form"
                    ]
                ),
            )
        )

    return result


# =============================================================================
# Rotas
# =============================================================================


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System"],
)
def health() -> HealthResponse:
    """Verifica se a API está disponível."""

    return HealthResponse(
        status="ok",
        version=app.version,
    )


@app.get(
    "/api/championship/summary",
    response_model=ChampionshipSummaryResponse,
    tags=["Championship"],
)
def championship_summary() -> ChampionshipSummaryResponse:
    """Retorna o resumo atual do campeonato."""

    matches = load_api_matches()

    summary = get_championship_summary(
        matches
    )

    standings = get_team_stats(
        matches
    )

    latest_round = get_latest_played_round(
        matches
    )

    return ChampionshipSummaryResponse(
        season=get_matches_season(
            matches
        ),
        total_matches=int(
            summary[
                "total_matches"
            ]
        ),
        played_matches=int(
            summary[
                "played_matches"
            ]
        ),
        future_matches=int(
            summary[
                "future_matches"
            ]
        ),
        total_goals=int(
            summary[
                "total_goals"
            ]
        ),
        average_goals_per_match=float(
            summary[
                "average_goals_per_match"
            ]
        ),
        home_wins=int(
            summary[
                "home_wins"
            ]
        ),
        draws=int(
            summary[
                "draws"
            ]
        ),
        away_wins=int(
            summary[
                "away_wins"
            ]
        ),
        latest_played_round=(
            int(
                latest_round
            )
            if latest_round
            else None
        ),
        leader=build_leader(
            standings
        ),
    )


@app.get(
    "/api/standings",
    response_model=list[StandingResponse],
    tags=["Championship"],
)
def standings() -> list[StandingResponse]:
    """Retorna a classificação calculada."""

    matches = load_api_matches()

    standings_dataframe = (
        get_team_stats(
            matches
        )
    )

    return build_standings_response(
        standings_dataframe
    )


@app.get(
    "/api/recent-form",
    response_model=list[RecentFormResponse],
    tags=["Championship"],
)
def recent_form(
    last_n: Annotated[
        int,
        Query(
            ge=1,
            le=20,
            description=(
                "Quantidade de jogos recentes "
                "considerados por clube."
            ),
        ),
    ] = 5,
) -> list[RecentFormResponse]:
    """Retorna o ranking de forma recente."""

    matches = load_api_matches()

    recent_dataframe = (
        get_recent_form_table(
            matches,
            last_n=last_n,
        )
    )

    return build_recent_form_response(
        recent_dataframe
    )
