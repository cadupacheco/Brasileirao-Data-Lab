from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque


# =============================================================================
# Elo
# =============================================================================

ELO_INITIAL_RATING = 1500.0
ELO_K_FACTOR = 20.0
ELO_HOME_ADVANTAGE = 65.0
ELO_SEASON_REGRESSION = 0.25


def get_elo_rating(
    ratings: dict[str, float],
    team_key: str,
) -> float:
    """Retorna o Elo atual do clube, iniciando em 1500 quando necessário."""

    return float(
        ratings.get(
            team_key,
            ELO_INITIAL_RATING,
        )
    )


def expected_home_score(
    home_rating: float,
    away_rating: float,
) -> float:
    """
    Calcula o score esperado do mandante no Elo.

    O mando de campo entra como um bônus fixo no rating do mandante.
    """

    adjusted_home_rating = (
        home_rating
        + ELO_HOME_ADVANTAGE
    )

    exponent = (
        away_rating
        - adjusted_home_rating
    ) / 400.0

    return float(
        1.0
        / (
            1.0
            + 10.0 ** exponent
        )
    )


def actual_home_score(
    home_goals: int,
    away_goals: int,
) -> float:
    """Converte o resultado real para o score clássico do Elo."""

    if home_goals > away_goals:
        return 1.0

    if home_goals == away_goals:
        return 0.5

    return 0.0


def update_elo_ratings(
    ratings: dict[str, float],
    home_team_key: str,
    away_team_key: str,
    home_goals: int,
    away_goals: int,
) -> None:
    """Atualiza os ratings após a partida."""

    home_rating = get_elo_rating(
        ratings,
        home_team_key,
    )
    away_rating = get_elo_rating(
        ratings,
        away_team_key,
    )

    expected_home = expected_home_score(
        home_rating,
        away_rating,
    )

    actual_home = actual_home_score(
        home_goals,
        away_goals,
    )

    delta = ELO_K_FACTOR * (
        actual_home
        - expected_home
    )

    ratings[
        home_team_key
    ] = home_rating + delta

    ratings[
        away_team_key
    ] = away_rating - delta


def regress_elo_ratings_for_new_season(
    ratings: dict[str, float],
) -> None:
    """
    Aproxima ratings antigos da média no início de uma nova temporada.

    Isso reduz o peso de informação muito antiga sem apagar completamente
    a força histórica do clube.
    """

    for team_key, rating in list(
        ratings.items()
    ):
        ratings[
            team_key
        ] = (
            ELO_INITIAL_RATING
            + (
                rating
                - ELO_INITIAL_RATING
            )
            * (
                1.0
                - ELO_SEASON_REGRESSION
            )
        )


# =============================================================================
# Confronto direto
# =============================================================================


@dataclass
class H2HState:
    """Histórico de confrontos entre dois clubes canônicos."""

    meetings: int = 0
    draws: int = 0

    wins_by_team: dict[str, int] = field(
        default_factory=dict
    )
    goals_by_team: dict[str, int] = field(
        default_factory=dict
    )

    recent_points_by_team: dict[
        str,
        Deque[int],
    ] = field(
        default_factory=dict
    )


def h2h_pair_key(
    team_a: str,
    team_b: str,
) -> tuple[str, str]:
    """Cria uma chave estável para o par de clubes."""

    if team_a == team_b:
        raise ValueError(
            "Um clube não pode ter H2H contra ele mesmo."
        )

    return tuple(
        sorted(
            (
                team_a,
                team_b,
            )
        )
    )


def get_h2h_state(
    states: dict[
        tuple[str, str],
        H2HState,
    ],
    team_a: str,
    team_b: str,
) -> H2HState:
    """Retorna ou cria o estado de confronto direto do par."""

    key = h2h_pair_key(
        team_a,
        team_b,
    )

    if key not in states:
        states[
            key
        ] = H2HState()

    state = states[
        key
    ]

    for team_key in key:
        state.wins_by_team.setdefault(
            team_key,
            0,
        )
        state.goals_by_team.setdefault(
            team_key,
            0,
        )
        state.recent_points_by_team.setdefault(
            team_key,
            deque(
                maxlen=5
            ),
        )

    return state


def build_h2h_features(
    states: dict[
        tuple[str, str],
        H2HState,
    ],
    home_team_key: str,
    away_team_key: str,
) -> dict[str, float | int]:
    """Cria as features H2H disponíveis antes da partida."""

    state = get_h2h_state(
        states=states,
        team_a=home_team_key,
        team_b=away_team_key,
    )

    home_wins = int(
        state.wins_by_team[
            home_team_key
        ]
    )

    away_wins = int(
        state.wins_by_team[
            away_team_key
        ]
    )

    home_goals = int(
        state.goals_by_team[
            home_team_key
        ]
    )

    away_goals = int(
        state.goals_by_team[
            away_team_key
        ]
    )

    home_recent_points = int(
        sum(
            state.recent_points_by_team[
                home_team_key
            ]
        )
    )

    away_recent_points = int(
        sum(
            state.recent_points_by_team[
                away_team_key
            ]
        )
    )

    if state.meetings == 0:
        home_ppg = 0.0
        away_ppg = 0.0
        goal_diff_per_game = 0.0

    else:
        home_total_points = (
            home_wins * 3
            + state.draws
        )

        away_total_points = (
            away_wins * 3
            + state.draws
        )

        home_ppg = (
            home_total_points
            / state.meetings
        )

        away_ppg = (
            away_total_points
            / state.meetings
        )

        goal_diff_per_game = (
            home_goals
            - away_goals
        ) / state.meetings

    return {
        "h2h_meetings_before": state.meetings,
        "h2h_home_wins_before": home_wins,
        "h2h_draws_before": state.draws,
        "h2h_away_wins_before": away_wins,
        "h2h_home_ppg_before": float(
            home_ppg
        ),
        "h2h_away_ppg_before": float(
            away_ppg
        ),
        "h2h_goal_difference_per_game_before": float(
            goal_diff_per_game
        ),
        "h2h_home_recent_points_5": home_recent_points,
        "h2h_away_recent_points_5": away_recent_points,
        "h2h_recent_points_5_diff": float(
            home_recent_points
            - away_recent_points
        ),
    }


def update_h2h_state(
    states: dict[
        tuple[str, str],
        H2HState,
    ],
    home_team_key: str,
    away_team_key: str,
    home_goals: int,
    away_goals: int,
) -> None:
    """Atualiza o confronto direto somente depois da partida."""

    state = get_h2h_state(
        states=states,
        team_a=home_team_key,
        team_b=away_team_key,
    )

    state.meetings += 1

    state.goals_by_team[
        home_team_key
    ] += home_goals

    state.goals_by_team[
        away_team_key
    ] += away_goals

    if home_goals > away_goals:
        state.wins_by_team[
            home_team_key
        ] += 1

        home_points = 3
        away_points = 0

    elif home_goals < away_goals:
        state.wins_by_team[
            away_team_key
        ] += 1

        home_points = 0
        away_points = 3

    else:
        state.draws += 1

        home_points = 1
        away_points = 1

    state.recent_points_by_team[
        home_team_key
    ].append(
        home_points
    )

    state.recent_points_by_team[
        away_team_key
    ].append(
        away_points
    )