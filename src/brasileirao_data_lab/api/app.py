from __future__ import annotations

from datetime import (
    date,
    time,
)
from typing import (
    Annotated,
    Literal,
)

import pandas as pd

from fastapi import (
    FastAPI,
    Query,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
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
from brasileirao_data_lab.database.match_queries import (
    get_matches_from_database,
)
from brasileirao_data_lab.database.repository import (
    get_standings_history,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
)


MatchFilterStatus = Literal[
    "all",
    "played",
    "upcoming",
]

MatchResponseStatus = Literal[
    "played",
    "upcoming",
]


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


class EvolutionPointResponse(BaseModel):
    season: int
    round: int
    team_id: int
    team: str
    position: int
    matches: int
    points: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    performance_pct: float


class MatchResponse(BaseModel):
    match_id: int
    season: int
    round: int
    match_number: int | None
    date: date | None
    time: time | None

    home_team_id: int
    home_team: str
    home_goals: int | None

    away_team_id: int
    away_team: str
    away_goals: int | None

    venue: str | None
    city: str | None
    state: str | None

    status: MatchResponseStatus


app = FastAPI(
    title="Brasileirão Data Lab API",
    description=(
        "API REST para acesso aos dados e Analytics "
        "do Campeonato Brasileiro Série A."
    ),
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://brasileirao-data-lab.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_api_matches() -> pd.DataFrame:
    with SessionLocal() as session:
        return load_matches_for_analytics(
            session
        )


def get_matches_season(
    matches: pd.DataFrame,
) -> int:
    seasons = matches[
        "season"
    ].dropna()

    if seasons.empty:
        raise ValueError(
            "Nenhuma temporada encontrada."
        )

    return int(
        seasons.max()
    )


def build_leader(
    standings: pd.DataFrame,
) -> LeaderResponse | None:
    if standings.empty:
        return None

    leader = standings.iloc[0]

    return LeaderResponse(
        team_id=int(
            leader["team_id"]
        ),
        team=str(
            leader["team"]
        ),
        position=int(
            leader[
                "calculated_position"
            ]
        ),
        points=int(
            leader["points"]
        ),
    )


def build_standings_response(
    standings: pd.DataFrame,
) -> list[StandingResponse]:
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
                    team["team_id"]
                ),
                team=str(
                    team["team"]
                ),
                matches=int(
                    team["matches"]
                ),
                wins=int(
                    team["wins"]
                ),
                draws=int(
                    team["draws"]
                ),
                losses=int(
                    team["losses"]
                ),
                goals_for=int(
                    team["goals_for"]
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
                    team["points"]
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
                    team["team_id"]
                ),
                team=str(
                    team["team"]
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
                    team["recent_form"]
                ),
            )
        )

    return result


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System"],
)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=app.version,
    )


@app.get(
    "/api/championship/summary",
    response_model=ChampionshipSummaryResponse,
    tags=["Championship"],
)
def championship_summary(
) -> ChampionshipSummaryResponse:
    matches = load_api_matches()

    summary = get_championship_summary(
        matches
    )

    standings = get_team_stats(
        matches
    )

    latest_round = (
        get_latest_played_round(
            matches
        )
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
    response_model=list[
        StandingResponse
    ],
    tags=["Championship"],
)
def standings(
) -> list[StandingResponse]:
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
    response_model=list[
        RecentFormResponse
    ],
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


@app.get(
    "/api/evolution",
    response_model=list[
        EvolutionPointResponse
    ],
    tags=["Championship"],
)
def evolution(
    team_ids: Annotated[
        list[int] | None,
        Query(
            description=(
                "IDs dos clubes que devem "
                "ser retornados."
            ),
        ),
    ] = None,
) -> list[EvolutionPointResponse]:
    matches = load_api_matches()

    season = get_matches_season(
        matches
    )

    with SessionLocal() as session:
        history = (
            get_standings_history(
                session=session,
                season=season,
                team_ids=team_ids,
            )
        )

    return [
        EvolutionPointResponse(
            season=int(
                point["season"]
            ),
            round=int(
                point["round"]
            ),
            team_id=int(
                point["team_id"]
            ),
            team=str(
                point["team"]
            ),
            position=int(
                point["position"]
            ),
            matches=int(
                point["matches"]
            ),
            points=int(
                point["points"]
            ),
            wins=int(
                point["wins"]
            ),
            draws=int(
                point["draws"]
            ),
            losses=int(
                point["losses"]
            ),
            goals_for=int(
                point["goals_for"]
            ),
            goals_against=int(
                point[
                    "goals_against"
                ]
            ),
            goal_difference=int(
                point[
                    "goal_difference"
                ]
            ),
            performance_pct=float(
                point[
                    "performance_pct"
                ]
            ),
        )
        for point in history
    ]


@app.get(
    "/api/matches",
    response_model=list[
        MatchResponse
    ],
    tags=["Matches"],
)
def championship_matches(
    round_number: Annotated[
        int | None,
        Query(
            ge=1,
            le=38,
            description=(
                "Filtra as partidas "
                "por rodada."
            ),
        ),
    ] = None,
    team_id: Annotated[
        int | None,
        Query(
            gt=0,
            description=(
                "Filtra as partidas "
                "por clube."
            ),
        ),
    ] = None,
    status: Annotated[
        MatchFilterStatus,
        Query(
            description=(
                "Filtra por all, "
                "played ou upcoming."
            ),
        ),
    ] = "all",
) -> list[MatchResponse]:
    matches = load_api_matches()

    season = get_matches_season(
        matches
    )

    with SessionLocal() as session:
        database_matches = (
            get_matches_from_database(
                session=session,
                season=season,
                round_number=round_number,
                team_id=team_id,
                status=status,
            )
        )

    result = []

    for match in database_matches:
        is_played = (
            match["home_goals"]
            is not None
            and match["away_goals"]
            is not None
        )

        match_status: MatchResponseStatus = (
            "played"
            if is_played
            else "upcoming"
        )

        result.append(
            MatchResponse(
                match_id=int(
                    match["match_id"]
                ),
                season=int(
                    match["season"]
                ),
                round=int(
                    match["round"]
                ),
                match_number=(
                    int(
                        match[
                            "match_number"
                        ]
                    )
                    if match[
                        "match_number"
                    ]
                    is not None
                    else None
                ),
                date=match[
                    "date"
                ],
                time=match[
                    "time"
                ],
                home_team_id=int(
                    match[
                        "home_team_id"
                    ]
                ),
                home_team=str(
                    match[
                        "home_team"
                    ]
                ),
                home_goals=(
                    int(
                        match[
                            "home_goals"
                        ]
                    )
                    if match[
                        "home_goals"
                    ]
                    is not None
                    else None
                ),
                away_team_id=int(
                    match[
                        "away_team_id"
                    ]
                ),
                away_team=str(
                    match[
                        "away_team"
                    ]
                ),
                away_goals=(
                    int(
                        match[
                            "away_goals"
                        ]
                    )
                    if match[
                        "away_goals"
                    ]
                    is not None
                    else None
                ),
                venue=(
                    str(
                        match["venue"]
                    )
                    if match[
                        "venue"
                    ]
                    else None
                ),
                city=(
                    str(
                        match["city"]
                    )
                    if match[
                        "city"
                    ]
                    else None
                ),
                state=(
                    str(
                        match["state"]
                    )
                    if match[
                        "state"
                    ]
                    else None
                ),
                status=match_status,
            )
        )

    return result