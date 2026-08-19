from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque

import pandas as pd

from brasileirao_data_lab.ml.ratings import (
    H2HState,
    build_h2h_features,
    expected_home_score,
    get_elo_rating,
    regress_elo_ratings_for_new_season,
    update_elo_ratings,
    update_h2h_state,
)
from brasileirao_data_lab.ml.team_identity import (
    canonical_team_key,
)


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_history_file() -> Path:
    """Retorna o CSV histórico coletado na V0.6."""

    return (
        get_project_root()
        / "data"
        / "ml"
        / "matches_history.csv"
    )


def get_features_file() -> Path:
    """Retorna o CSV de features da V0.6."""

    return (
        get_project_root()
        / "data"
        / "ml"
        / "features.csv"
    )


# =============================================================================
# Estado acumulado por clube
# =============================================================================


@dataclass
class TeamState:
    """Estado de um clube antes de uma determinada partida."""

    matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    points: int = 0
    goals_for: int = 0
    goals_against: int = 0

    home_matches: int = 0
    home_points: int = 0
    home_goals_for: int = 0
    home_goals_against: int = 0

    away_matches: int = 0
    away_points: int = 0
    away_goals_for: int = 0
    away_goals_against: int = 0

    recent_points: Deque[int] = field(
        default_factory=lambda: deque(
            maxlen=10
        )
    )
    recent_goals_for: Deque[int] = field(
        default_factory=lambda: deque(
            maxlen=10
        )
    )
    recent_goals_against: Deque[int] = field(
        default_factory=lambda: deque(
            maxlen=10
        )
    )


# =============================================================================
# Utilidades numéricas
# =============================================================================


def safe_divide(
    numerator: float | int,
    denominator: float | int,
) -> float:
    """Divide com proteção para denominador zero."""

    if denominator == 0:
        return 0.0

    return float(
        numerator
        / denominator
    )


def rolling_sum(
    values: Deque[int],
    size: int,
) -> int:
    """Soma os últimos N valores."""

    if size <= 0:
        raise ValueError(
            "O tamanho da janela deve ser maior que zero."
        )

    selected = list(
        values
    )[-size:]

    return int(
        sum(selected)
    )


def rolling_average(
    values: Deque[int],
    size: int,
) -> float:
    """Calcula a média dos últimos N valores disponíveis."""

    if size <= 0:
        raise ValueError(
            "O tamanho da janela deve ser maior que zero."
        )

    selected = list(
        values
    )[-size:]

    if not selected:
        return 0.0

    return float(
        sum(selected)
        / len(selected)
    )


# =============================================================================
# Resultado da partida
# =============================================================================


def points_for_team(
    team_goals: int,
    opponent_goals: int,
) -> int:
    """Retorna os pontos obtidos por um clube em uma partida."""

    if team_goals > opponent_goals:
        return 3

    if team_goals == opponent_goals:
        return 1

    return 0


# =============================================================================
# Snapshot pré-jogo
# =============================================================================


def build_team_features(
    state: TeamState,
    prefix: str,
    venue: str,
) -> dict[str, float | int]:
    """
    Cria features usando somente informações anteriores ao jogo.

    venue deve ser "home" para o mandante ou "away" para o visitante.
    """

    if venue not in {
        "home",
        "away",
    }:
        raise ValueError(
            "venue deve ser 'home' ou 'away'."
        )

    goal_difference = (
        state.goals_for
        - state.goals_against
    )

    features: dict[
        str,
        float | int,
    ] = {
        f"{prefix}_matches_before": state.matches,
        f"{prefix}_wins_before": state.wins,
        f"{prefix}_draws_before": state.draws,
        f"{prefix}_losses_before": state.losses,
        f"{prefix}_points_before": state.points,
        f"{prefix}_ppg_before": safe_divide(
            state.points,
            state.matches,
        ),
        f"{prefix}_goals_for_before": state.goals_for,
        f"{prefix}_goals_against_before": state.goals_against,
        f"{prefix}_goal_difference_before": goal_difference,
        f"{prefix}_goals_for_per_game_before": safe_divide(
            state.goals_for,
            state.matches,
        ),
        f"{prefix}_goals_against_per_game_before": safe_divide(
            state.goals_against,
            state.matches,
        ),
        f"{prefix}_goal_difference_per_game_before": safe_divide(
            goal_difference,
            state.matches,
        ),
        f"{prefix}_recent_points_5": rolling_sum(
            state.recent_points,
            5,
        ),
        f"{prefix}_recent_points_10": rolling_sum(
            state.recent_points,
            10,
        ),
        f"{prefix}_recent_goals_for_avg_5": rolling_average(
            state.recent_goals_for,
            5,
        ),
        f"{prefix}_recent_goals_against_avg_5": rolling_average(
            state.recent_goals_against,
            5,
        ),
        f"{prefix}_recent_goals_for_avg_10": rolling_average(
            state.recent_goals_for,
            10,
        ),
        f"{prefix}_recent_goals_against_avg_10": rolling_average(
            state.recent_goals_against,
            10,
        ),
    }

    if venue == "home":
        features.update(
            {
                f"{prefix}_venue_matches_before": state.home_matches,
                f"{prefix}_venue_points_before": state.home_points,
                f"{prefix}_venue_ppg_before": safe_divide(
                    state.home_points,
                    state.home_matches,
                ),
                f"{prefix}_venue_goals_for_per_game_before": safe_divide(
                    state.home_goals_for,
                    state.home_matches,
                ),
                f"{prefix}_venue_goals_against_per_game_before": safe_divide(
                    state.home_goals_against,
                    state.home_matches,
                ),
            }
        )

    else:
        features.update(
            {
                f"{prefix}_venue_matches_before": state.away_matches,
                f"{prefix}_venue_points_before": state.away_points,
                f"{prefix}_venue_ppg_before": safe_divide(
                    state.away_points,
                    state.away_matches,
                ),
                f"{prefix}_venue_goals_for_per_game_before": safe_divide(
                    state.away_goals_for,
                    state.away_matches,
                ),
                f"{prefix}_venue_goals_against_per_game_before": safe_divide(
                    state.away_goals_against,
                    state.away_matches,
                ),
            }
        )

    return features


def build_difference_features(
    home_features: dict[str, float | int],
    away_features: dict[str, float | int],
) -> dict[str, float]:
    """Cria diferenças entre mandante e visitante."""

    return {
        "ppg_diff": float(
            home_features[
                "home_ppg_before"
            ]
            - away_features[
                "away_ppg_before"
            ]
        ),
        "goal_difference_per_game_diff": float(
            home_features[
                "home_goal_difference_per_game_before"
            ]
            - away_features[
                "away_goal_difference_per_game_before"
            ]
        ),
        "recent_points_5_diff": float(
            home_features[
                "home_recent_points_5"
            ]
            - away_features[
                "away_recent_points_5"
            ]
        ),
        "recent_points_10_diff": float(
            home_features[
                "home_recent_points_10"
            ]
            - away_features[
                "away_recent_points_10"
            ]
        ),
        "venue_ppg_diff": float(
            home_features[
                "home_venue_ppg_before"
            ]
            - away_features[
                "away_venue_ppg_before"
            ]
        ),
        "recent_goal_balance_5_diff": float(
            (
                home_features[
                    "home_recent_goals_for_avg_5"
                ]
                - home_features[
                    "home_recent_goals_against_avg_5"
                ]
            )
            - (
                away_features[
                    "away_recent_goals_for_avg_5"
                ]
                - away_features[
                    "away_recent_goals_against_avg_5"
                ]
            )
        ),
    }


# =============================================================================
# Atualização do estado
# =============================================================================


def update_team_state(
    state: TeamState,
    goals_for: int,
    goals_against: int,
    venue: str,
) -> None:
    """Atualiza o estado do clube somente após extrair as features."""

    if venue not in {
        "home",
        "away",
    }:
        raise ValueError(
            "venue deve ser 'home' ou 'away'."
        )

    points = points_for_team(
        goals_for,
        goals_against,
    )

    state.matches += 1
    state.points += points
    state.goals_for += goals_for
    state.goals_against += goals_against

    if points == 3:
        state.wins += 1
    elif points == 1:
        state.draws += 1
    else:
        state.losses += 1

    state.recent_points.append(
        points
    )
    state.recent_goals_for.append(
        goals_for
    )
    state.recent_goals_against.append(
        goals_against
    )

    if venue == "home":
        state.home_matches += 1
        state.home_points += points
        state.home_goals_for += goals_for
        state.home_goals_against += goals_against

    else:
        state.away_matches += 1
        state.away_points += points
        state.away_goals_for += goals_for
        state.away_goals_against += goals_against


# =============================================================================
# Dataset
# =============================================================================


def prepare_played_matches(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Mantém apenas jogos disputados e ordena pelo momento real da partida.

    Isso é importante para impedir que uma feature use informação futura.
    """

    required_columns = {
        "season",
        "round",
        "match_id",
        "date",
        "time",
        "home_team_id",
        "home_team",
        "home_goals",
        "away_team_id",
        "away_team",
        "away_goals",
        "status",
        "result",
    }

    missing_columns = (
        required_columns
        - set(
            dataframe.columns
        )
    )

    if missing_columns:
        missing = ", ".join(
            sorted(
                missing_columns
            )
        )

        raise ValueError(
            "Colunas obrigatórias ausentes: "
            f"{missing}"
        )

    played = dataframe[
        dataframe[
            "status"
        ] == "played"
    ].copy()

    if played.empty:
        raise ValueError(
            "Nenhuma partida disputada encontrada."
        )

    if played[
        [
            "date",
            "time",
            "home_goals",
            "away_goals",
            "result",
        ]
    ].isna().any().any():
        raise ValueError(
            "Existem jogos disputados com dados essenciais ausentes."
        )

    played[
        "match_datetime"
    ] = pd.to_datetime(
        played[
            "date"
        ].astype(str)
        + " "
        + played[
            "time"
        ].astype(str),
        errors="raise",
    )

    played = played.sort_values(
        by=[
            "season",
            "match_datetime",
            "match_id",
        ]
    ).reset_index(
        drop=True
    )

    return played


def build_feature_dataset(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Constrói o dataset de treino sem vazamento de dados.

    As estatísticas de temporada zeram a cada ano.
    Elo e H2H carregam informação histórica entre temporadas, sempre usando
    apenas jogos já disputados antes da partida atual.
    """

    played = prepare_played_matches(
        history
    )

    feature_rows: list[
        dict[str, object]
    ] = []

    current_season: int | None = None

    season_states: dict[
        str,
        TeamState,
    ] = {}

    elo_ratings: dict[
        str,
        float,
    ] = {}

    h2h_states: dict[
        tuple[str, str],
        H2HState,
    ] = {}

    for row in played.itertuples(
        index=False
    ):
        season = int(
            row.season
        )

        if current_season != season:
            if current_season is not None:
                regress_elo_ratings_for_new_season(
                    elo_ratings
                )

            current_season = season
            season_states = {}

        home_team_key = canonical_team_key(
            str(
                row.home_team
            )
        )

        away_team_key = canonical_team_key(
            str(
                row.away_team
            )
        )

        home_state = season_states.setdefault(
            home_team_key,
            TeamState(),
        )

        away_state = season_states.setdefault(
            away_team_key,
            TeamState(),
        )

        home_features = build_team_features(
            state=home_state,
            prefix="home",
            venue="home",
        )

        away_features = build_team_features(
            state=away_state,
            prefix="away",
            venue="away",
        )

        difference_features = build_difference_features(
            home_features,
            away_features,
        )

        home_elo = get_elo_rating(
            elo_ratings,
            home_team_key,
        )

        away_elo = get_elo_rating(
            elo_ratings,
            away_team_key,
        )

        elo_features = {
            "home_elo_before": float(
                home_elo
            ),
            "away_elo_before": float(
                away_elo
            ),
            "elo_diff": float(
                home_elo
                - away_elo
            ),
            "elo_expected_home_score": (
                expected_home_score(
                    home_elo,
                    away_elo,
                )
            ),
        }

        h2h_features = build_h2h_features(
            states=h2h_states,
            home_team_key=home_team_key,
            away_team_key=away_team_key,
        )

        feature_rows.append(
            {
                "season": season,
                "round": int(
                    row.round
                ),
                "match_id": int(
                    row.match_id
                ),
                "date": str(
                    row.date
                ),
                "time": str(
                    row.time
                ),
                "home_team_id": int(
                    row.home_team_id
                ),
                "home_team": str(
                    row.home_team
                ),
                "home_team_key": (
                    home_team_key
                ),
                "away_team_id": int(
                    row.away_team_id
                ),
                "away_team": str(
                    row.away_team
                ),
                "away_team_key": (
                    away_team_key
                ),
                **home_features,
                **away_features,
                **difference_features,
                **elo_features,
                **h2h_features,
                "target": str(
                    row.result
                ),
            }
        )

        home_goals = int(
            row.home_goals
        )

        away_goals = int(
            row.away_goals
        )

        update_team_state(
            state=home_state,
            goals_for=home_goals,
            goals_against=away_goals,
            venue="home",
        )

        update_team_state(
            state=away_state,
            goals_for=away_goals,
            goals_against=home_goals,
            venue="away",
        )

        update_elo_ratings(
            ratings=elo_ratings,
            home_team_key=home_team_key,
            away_team_key=away_team_key,
            home_goals=home_goals,
            away_goals=away_goals,
        )

        update_h2h_state(
            states=h2h_states,
            home_team_key=home_team_key,
            away_team_key=away_team_key,
            home_goals=home_goals,
            away_goals=away_goals,
        )

    features = pd.DataFrame(
        feature_rows
    )

    validate_feature_dataset(
        features
    )

    return features


# =============================================================================
# Validação
# =============================================================================


def validate_feature_dataset(
    dataframe: pd.DataFrame,
) -> None:
    """Valida propriedades essenciais do dataset de features."""

    if dataframe.empty:
        raise ValueError(
            "Dataset de features vazio."
        )

    if dataframe[
        "match_id"
    ].duplicated().any():
        raise ValueError(
            "Existem match_id duplicados no dataset de features."
        )

    allowed_targets = {
        "HOME",
        "DRAW",
        "AWAY",
    }

    targets = set(
        dataframe[
            "target"
        ].unique()
    )

    if not targets.issubset(
        allowed_targets
    ):
        raise ValueError(
            "Foram encontrados targets inválidos: "
            f"{sorted(targets)}"
        )

    non_feature_columns = {
        "season",
        "round",
        "match_id",
        "date",
        "time",
        "home_team_id",
        "home_team",
        "home_team_key",
        "away_team_id",
        "away_team",
        "away_team_key",
        "target",
    }

    numeric_columns = [
        column
        for column in dataframe.columns
        if column not in non_feature_columns
    ]

    if dataframe[
        numeric_columns
    ].isna().any().any():
        raise ValueError(
            "Existem valores nulos nas features numéricas."
        )


# =============================================================================
# Persistência
# =============================================================================


def load_history_dataframe(
    history_file: Path | None = None,
) -> pd.DataFrame:
    """Carrega o histórico coletado."""

    path = (
        history_file
        if history_file is not None
        else get_history_file()
    )

    if not path.exists():
        raise FileNotFoundError(
            "Histórico não encontrado em: "
            f"{path}"
        )

    return pd.read_csv(
        path
    )


def save_feature_dataset(
    dataframe: pd.DataFrame,
    output_file: Path | None = None,
) -> Path:
    """Salva o dataset de features."""

    path = (
        output_file
        if output_file is not None
        else get_features_file()
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
    )

    return path


# =============================================================================
# Resumo
# =============================================================================


def print_feature_summary(
    dataframe: pd.DataFrame,
) -> None:
    """Exibe um resumo útil do feature engineering."""

    print()
    print(
        "=" * 88
    )
    print(
        "[SUMMARY] Dataset de Machine Learning"
    )
    print(
        "=" * 88
    )

    print(
        f"Linhas: {len(dataframe)}"
    )
    print(
        f"Colunas: {len(dataframe.columns)}"
    )

    print()
    print(
        "Partidas por temporada:"
    )

    counts = (
        dataframe
        .groupby("season")
        .size()
    )

    for season, count in counts.items():
        print(
            f"  {int(season)}: {int(count)}"
        )

    print()
    print(
        "Distribuição do target:"
    )

    target_counts = (
        dataframe[
            "target"
        ]
        .value_counts()
    )

    for target in (
        "HOME",
        "DRAW",
        "AWAY",
    ):
        count = int(
            target_counts.get(
                target,
                0,
            )
        )

        percentage = (
            count
            / len(dataframe)
            * 100
        )

        print(
            f"  {target}: "
            f"{count} "
            f"({percentage:.2f}%)"
        )

    print()
    print(
        "Primeiro jogo de cada temporada:"
    )

    first_rows = (
        dataframe
        .sort_values(
            by=[
                "season",
                "date",
                "time",
                "match_id",
            ]
        )
        .groupby(
            "season",
            as_index=False,
        )
        .first()
    )

    for row in first_rows.itertuples(
        index=False
    ):
        print(
            f"  {int(row.season)} | "
            f"{row.home_team} x {row.away_team} | "
            f"home_matches_before="
            f"{int(row.home_matches_before)} | "
            f"away_matches_before="
            f"{int(row.away_matches_before)} | "
            f"home_elo="
            f"{row.home_elo_before:.1f} | "
            f"away_elo="
            f"{row.away_elo_before:.1f} | "
            f"h2h="
            f"{int(row.h2h_meetings_before)}"
        )