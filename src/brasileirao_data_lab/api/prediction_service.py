from __future__ import annotations

from pathlib import Path

import pandas as pd

from brasileirao_data_lab.ml.predictions import (
    get_predictions_file,
)
from brasileirao_data_lab.ml.simulation import (
    get_simulation_file,
)


# =============================================================================
# Carregamento
# =============================================================================


def load_match_predictions(
    path: Path | None = None,
) -> pd.DataFrame:
    """Carrega as previsões das partidas futuras."""

    predictions_file = (
        path
        if path is not None
        else get_predictions_file()
    )

    if not predictions_file.exists():
        raise FileNotFoundError(
            "Arquivo de previsões não encontrado em: "
            f"{predictions_file}"
        )

    dataframe = pd.read_csv(
        predictions_file
    )

    required_columns = {
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
        "home_probability",
        "draw_probability",
        "away_probability",
        "predicted_result",
        "home_probability_pct",
        "draw_probability_pct",
        "away_probability_pct",
    }

    missing = (
        required_columns
        - set(
            dataframe.columns
        )
    )

    if missing:
        raise ValueError(
            "Colunas ausentes em future_predictions.csv: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    return dataframe


def load_season_simulation(
    path: Path | None = None,
) -> pd.DataFrame:
    """Carrega o resumo da simulação Monte Carlo."""

    simulation_file = (
        path
        if path is not None
        else get_simulation_file()
    )

    if not simulation_file.exists():
        raise FileNotFoundError(
            "Arquivo de simulação não encontrado em: "
            f"{simulation_file}"
        )

    dataframe = pd.read_csv(
        simulation_file
    )

    required_columns = {
        "season",
        "team_key",
        "team_name",
        "simulations",
        "expected_points",
        "average_position",
        "champion_probability",
        "top4_probability",
        "top6_probability",
        "relegation_probability",
        "champion_probability_pct",
        "top4_probability_pct",
        "top6_probability_pct",
        "relegation_probability_pct",
    }

    missing = (
        required_columns
        - set(
            dataframe.columns
        )
    )

    if missing:
        raise ValueError(
            "Colunas ausentes em season_simulation.csv: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    return dataframe


# =============================================================================
# Previsões de partidas
# =============================================================================


def get_match_predictions(
    dataframe: pd.DataFrame,
    round_number: int | None = None,
    team_id: int | None = None,
) -> list[dict[str, object]]:
    """Filtra e serializa as previsões das partidas."""

    filtered = dataframe.copy()

    if round_number is not None:
        filtered = filtered[
            filtered[
                "round"
            ] == round_number
        ]

    if team_id is not None:
        filtered = filtered[
            (
                filtered[
                    "home_team_id"
                ] == team_id
            )
            | (
                filtered[
                    "away_team_id"
                ] == team_id
            )
        ]

    filtered = filtered.sort_values(
        by=[
            "round",
            "date",
            "time",
            "match_id",
        ],
        na_position="last",
    )

    result: list[
        dict[str, object]
    ] = []

    for row in filtered.itertuples(
        index=False
    ):
        result.append(
            {
                "season": int(
                    row.season
                ),
                "round": int(
                    row.round
                ),
                "match_id": int(
                    row.match_id
                ),
                "date": (
                    None
                    if pd.isna(
                        row.date
                    )
                    else str(
                        row.date
                    )
                ),
                "time": (
                    None
                    if pd.isna(
                        row.time
                    )
                    else str(
                        row.time
                    )
                ),
                "home_team_id": int(
                    row.home_team_id
                ),
                "home_team": str(
                    row.home_team
                ),
                "home_team_key": str(
                    row.home_team_key
                ),
                "away_team_id": int(
                    row.away_team_id
                ),
                "away_team": str(
                    row.away_team
                ),
                "away_team_key": str(
                    row.away_team_key
                ),
                "home_probability": float(
                    row.home_probability
                ),
                "draw_probability": float(
                    row.draw_probability
                ),
                "away_probability": float(
                    row.away_probability
                ),
                "predicted_result": str(
                    row.predicted_result
                ),
                "home_probability_pct": float(
                    row.home_probability_pct
                ),
                "draw_probability_pct": float(
                    row.draw_probability_pct
                ),
                "away_probability_pct": float(
                    row.away_probability_pct
                ),
            }
        )

    return result


# =============================================================================
# Simulação da classificação
# =============================================================================


def get_standings_predictions(
    dataframe: pd.DataFrame,
) -> list[dict[str, object]]:
    """Serializa a classificação projetada pelo Monte Carlo."""

    sorted_dataframe = dataframe.sort_values(
        by=[
            "average_position",
            "expected_points",
        ],
        ascending=[
            True,
            False,
        ],
    ).reset_index(
        drop=True
    )

    result: list[
        dict[str, object]
    ] = []

    for position, row in enumerate(
        sorted_dataframe.itertuples(
            index=False
        ),
        start=1,
    ):
        result.append(
            {
                "projected_position": position,
                "season": int(
                    row.season
                ),
                "team_key": str(
                    row.team_key
                ),
                "team_name": str(
                    row.team_name
                ),
                "simulations": int(
                    row.simulations
                ),
                "expected_points": float(
                    row.expected_points
                ),
                "average_position": float(
                    row.average_position
                ),
                "champion_probability": float(
                    row.champion_probability
                ),
                "top4_probability": float(
                    row.top4_probability
                ),
                "top6_probability": float(
                    row.top6_probability
                ),
                "relegation_probability": float(
                    row.relegation_probability
                ),
                "champion_probability_pct": float(
                    row.champion_probability_pct
                ),
                "top4_probability_pct": float(
                    row.top4_probability_pct
                ),
                "top6_probability_pct": float(
                    row.top6_probability_pct
                ),
                "relegation_probability_pct": float(
                    row.relegation_probability_pct
                ),
            }
        )

    return result