


from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from brasileirao_data_lab.ml.features import (
    load_history_dataframe,
)
from brasileirao_data_lab.ml.predictions import (
    get_predictions_file,
)
from brasileirao_data_lab.ml.team_identity import (
    canonical_team_key,
)


# =============================================================================
# Configuração
# =============================================================================

DEFAULT_SIMULATIONS = 10_000
DEFAULT_RANDOM_SEED = 42


# =============================================================================
# Estruturas
# =============================================================================


@dataclass(frozen=True)
class TeamSnapshot:
    team_key: str
    team_name: str
    points: int
    wins: int
    goals_for: int
    goals_against: int


@dataclass(frozen=True)
class ScorePools:
    home_wins: np.ndarray
    draws: np.ndarray
    away_wins: np.ndarray


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_simulation_file() -> Path:
    """Retorna o CSV com o resumo do Monte Carlo."""

    return (
        get_project_root()
        / "data"
        / "ml"
        / "season_simulation.csv"
    )


# =============================================================================
# Dados
# =============================================================================


def load_predictions(
    path: Path | None = None,
) -> pd.DataFrame:
    """Carrega as probabilidades das partidas futuras."""

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
        "home_team",
        "home_team_key",
        "away_team",
        "away_team_key",
        "home_probability",
        "draw_probability",
        "away_probability",
    }

    missing = (
        required_columns
        - set(
            dataframe.columns
        )
    )

    if missing:
        raise ValueError(
            "Colunas ausentes nas previsões: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    return dataframe


# =============================================================================
# Classificação atual
# =============================================================================


def build_current_standings(
    history: pd.DataFrame,
    season: int,
) -> list[TeamSnapshot]:
    """Reconstrói a classificação atual usando somente partidas disputadas."""

    season_rows = history[
        history[
            "season"
        ] == season
    ].copy()

    if season_rows.empty:
        raise ValueError(
            f"Nenhuma partida encontrada para {season}."
        )

    played = season_rows[
        season_rows[
            "status"
        ] == "played"
    ].copy()

    if played.empty:
        raise ValueError(
            f"Nenhuma partida disputada encontrada para {season}."
        )

    latest_names: dict[
        str,
        str,
    ] = {}

    stats: dict[
        str,
        dict[str, int],
    ] = {}

    def ensure_team(
        team_key: str,
    ) -> dict[str, int]:
        return stats.setdefault(
            team_key,
            {
                "points": 0,
                "wins": 0,
                "goals_for": 0,
                "goals_against": 0,
            },
        )

    for row in played.itertuples(
        index=False
    ):
        home_key = canonical_team_key(
            str(
                row.home_team
            )
        )

        away_key = canonical_team_key(
            str(
                row.away_team
            )
        )

        latest_names[
            home_key
        ] = str(
            row.home_team
        )

        latest_names[
            away_key
        ] = str(
            row.away_team
        )

        home = ensure_team(
            home_key
        )

        away = ensure_team(
            away_key
        )

        home_goals = int(
            row.home_goals
        )

        away_goals = int(
            row.away_goals
        )

        home[
            "goals_for"
        ] += home_goals

        home[
            "goals_against"
        ] += away_goals

        away[
            "goals_for"
        ] += away_goals

        away[
            "goals_against"
        ] += home_goals

        if home_goals > away_goals:
            home[
                "points"
            ] += 3

            home[
                "wins"
            ] += 1

        elif home_goals < away_goals:
            away[
                "points"
            ] += 3

            away[
                "wins"
            ] += 1

        else:
            home[
                "points"
            ] += 1

            away[
                "points"
            ] += 1

    # Inclui clubes que só aparecem em partidas futuras, caso exista algum.
    for row in season_rows.itertuples(
        index=False
    ):
        for team_name in (
            str(
                row.home_team
            ),
            str(
                row.away_team
            ),
        ):
            team_key = canonical_team_key(
                team_name
            )

            latest_names[
                team_key
            ] = team_name

            ensure_team(
                team_key
            )

    snapshots = [
        TeamSnapshot(
            team_key=team_key,
            team_name=latest_names[
                team_key
            ],
            points=int(
                values[
                    "points"
                ]
            ),
            wins=int(
                values[
                    "wins"
                ]
            ),
            goals_for=int(
                values[
                    "goals_for"
                ]
            ),
            goals_against=int(
                values[
                    "goals_against"
                ]
            ),
        )
        for team_key, values in stats.items()
    ]

    return sorted(
        snapshots,
        key=lambda team: (
            -team.points,
            -team.wins,
            -(
                team.goals_for
                - team.goals_against
            ),
            -team.goals_for,
            team.team_key,
        ),
    )


# =============================================================================
# Placar empírico
# =============================================================================


def build_score_pools(
    history: pd.DataFrame,
) -> ScorePools:
    """
    Cria pools históricos de placares por tipo de resultado.

    Isso permite atualizar gols e saldo no Monte Carlo sem inventar um modelo
    de gols separado nesta etapa.
    """

    played = history[
        history[
            "status"
        ] == "played"
    ].copy()

    played = played.dropna(
        subset=[
            "home_goals",
            "away_goals",
            "result",
        ]
    )

    if played.empty:
        raise ValueError(
            "Nenhum placar histórico disponível."
        )

    def pool_for(
        result: str,
    ) -> np.ndarray:
        subset = played[
            played[
                "result"
            ] == result
        ][
            [
                "home_goals",
                "away_goals",
            ]
        ].to_numpy(
            dtype=np.int16
        )

        if len(
            subset
        ) == 0:
            raise ValueError(
                f"Pool de placares vazio para {result}."
            )

        return subset

    return ScorePools(
        home_wins=pool_for(
            "HOME"
        ),
        draws=pool_for(
            "DRAW"
        ),
        away_wins=pool_for(
            "AWAY"
        ),
    )


# =============================================================================
# Monte Carlo
# =============================================================================


def choose_scorelines(
    rng: np.random.Generator,
    result_codes: np.ndarray,
    score_pools: ScorePools,
) -> tuple[
    np.ndarray,
    np.ndarray,
]:
    """Sorteia placares históricos condicionados ao resultado simulado."""

    simulations = len(
        result_codes
    )

    home_goals = np.zeros(
        simulations,
        dtype=np.int16,
    )

    away_goals = np.zeros(
        simulations,
        dtype=np.int16,
    )

    pool_map = {
        0: score_pools.home_wins,
        1: score_pools.draws,
        2: score_pools.away_wins,
    }

    for code, pool in pool_map.items():
        mask = (
            result_codes
            == code
        )

        count = int(
            mask.sum()
        )

        if count == 0:
            continue

        sampled_indices = rng.integers(
            0,
            len(
                pool
            ),
            size=count,
        )

        sampled = pool[
            sampled_indices
        ]

        home_goals[
            mask
        ] = sampled[
            :,
            0
        ]

        away_goals[
            mask
        ] = sampled[
            :,
            1
        ]

    return (
        home_goals,
        away_goals,
    )


def rank_simulations(
    points: np.ndarray,
    wins: np.ndarray,
    goals_for: np.ndarray,
    goals_against: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Retorna a posição final de cada clube em cada simulação.

    Critérios usados nesta etapa:
    pontos, vitórias, saldo de gols e gols marcados.

    Empates absolutos depois desses campos recebem um desempate aleatório
    reproduzível apenas para o Monte Carlo.
    """

    goal_difference = (
        goals_for
        - goals_against
    )

    random_tiebreak = rng.random(
        size=points.shape
    )

    order = np.lexsort(
        (
            random_tiebreak,
            -goals_for,
            -goal_difference,
            -wins,
            -points,
        ),
        axis=1,
    )

    positions = np.empty_like(
        order,
        dtype=np.int16,
    )

    row_indices = np.arange(
        order.shape[
            0
        ]
    )[
        :,
        None,
    ]

    positions[
        row_indices,
        order,
    ] = np.arange(
        1,
        order.shape[
            1
        ]
        + 1,
        dtype=np.int16,
    )

    return positions


def simulate_season(
    history: pd.DataFrame,
    predictions: pd.DataFrame,
    simulations: int = DEFAULT_SIMULATIONS,
    seed: int = DEFAULT_RANDOM_SEED,
) -> pd.DataFrame:
    """Simula todas as partidas restantes milhares de vezes."""

    if simulations <= 0:
        raise ValueError(
            "O número de simulações deve ser maior que zero."
        )

    if predictions.empty:
        raise ValueError(
            "Nenhuma partida futura foi informada."
        )

    seasons = predictions[
        "season"
    ].dropna().unique()

    if len(
        seasons
    ) != 1:
        raise ValueError(
            "As previsões devem pertencer a uma única temporada."
        )

    season = int(
        seasons[
            0
        ]
    )

    standings = build_current_standings(
        history=history,
        season=season,
    )

    team_keys = [
        team.team_key
        for team in standings
    ]

    team_names = {
        team.team_key: team.team_name
        for team in standings
    }

    team_index = {
        team_key: index
        for index, team_key in enumerate(
            team_keys
        )
    }

    team_count = len(
        team_keys
    )

    if team_count == 0:
        raise ValueError(
            "Nenhum clube encontrado para simulação."
        )

    base_points = np.array(
        [
            team.points
            for team in standings
        ],
        dtype=np.int16,
    )

    base_wins = np.array(
        [
            team.wins
            for team in standings
        ],
        dtype=np.int16,
    )

    base_goals_for = np.array(
        [
            team.goals_for
            for team in standings
        ],
        dtype=np.int16,
    )

    base_goals_against = np.array(
        [
            team.goals_against
            for team in standings
        ],
        dtype=np.int16,
    )

    points = np.tile(
        base_points,
        (
            simulations,
            1,
        ),
    )

    wins = np.tile(
        base_wins,
        (
            simulations,
            1,
        ),
    )

    goals_for = np.tile(
        base_goals_for,
        (
            simulations,
            1,
        ),
    )

    goals_against = np.tile(
        base_goals_against,
        (
            simulations,
            1,
        ),
    )

    score_pools = build_score_pools(
        history
    )

    rng = np.random.default_rng(
        seed
    )

    rows = np.arange(
        simulations
    )

    for match in predictions.itertuples(
        index=False
    ):
        home_index = team_index[
            str(
                match.home_team_key
            )
        ]

        away_index = team_index[
            str(
                match.away_team_key
            )
        ]

        probabilities = np.array(
            [
                float(
                    match.home_probability
                ),
                float(
                    match.draw_probability
                ),
                float(
                    match.away_probability
                ),
            ],
            dtype=float,
        )

        probability_sum = float(
            probabilities.sum()
        )

        if not np.isclose(
            probability_sum,
            1.0,
            atol=1e-6,
        ):
            probabilities = (
                probabilities
                / probability_sum
            )

        result_codes = rng.choice(
            3,
            size=simulations,
            p=probabilities,
        )

        home_win = (
            result_codes
            == 0
        )

        draw = (
            result_codes
            == 1
        )

        away_win = (
            result_codes
            == 2
        )

        points[
            rows,
            home_index,
        ] += (
            home_win.astype(
                np.int16
            )
            * 3
            + draw.astype(
                np.int16
            )
        )

        points[
            rows,
            away_index,
        ] += (
            away_win.astype(
                np.int16
            )
            * 3
            + draw.astype(
                np.int16
            )
        )

        wins[
            rows,
            home_index,
        ] += home_win.astype(
            np.int16
        )

        wins[
            rows,
            away_index,
        ] += away_win.astype(
            np.int16
        )

        (
            simulated_home_goals,
            simulated_away_goals,
        ) = choose_scorelines(
            rng=rng,
            result_codes=result_codes,
            score_pools=score_pools,
        )

        goals_for[
            rows,
            home_index,
        ] += simulated_home_goals

        goals_against[
            rows,
            home_index,
        ] += simulated_away_goals

        goals_for[
            rows,
            away_index,
        ] += simulated_away_goals

        goals_against[
            rows,
            away_index,
        ] += simulated_home_goals

    positions = rank_simulations(
        points=points,
        wins=wins,
        goals_for=goals_for,
        goals_against=goals_against,
        rng=rng,
    )

    result_rows: list[
        dict[str, object]
    ] = []

    for team_key, index in team_index.items():
        team_positions = positions[
            :,
            index
        ]

        team_points = points[
            :,
            index
        ]

        result_rows.append(
            {
                "season": season,
                "team_key": team_key,
                "team_name": team_names[
                    team_key
                ],
                "simulations": simulations,
                "expected_points": float(
                    team_points.mean()
                ),
                "average_position": float(
                    team_positions.mean()
                ),
                "champion_probability": float(
                    (
                        team_positions
                        == 1
                    ).mean()
                ),
                "top4_probability": float(
                    (
                        team_positions
                        <= 4
                    ).mean()
                ),
                "top6_probability": float(
                    (
                        team_positions
                        <= 6
                    ).mean()
                ),
                "relegation_probability": float(
                    (
                        team_positions
                        >= (
                            team_count
                            - 3
                        )
                    ).mean()
                ),
                "champion_probability_pct": round(
                    float(
                        (
                            team_positions
                            == 1
                        ).mean()
                        * 100.0
                    ),
                    2,
                ),
                "top4_probability_pct": round(
                    float(
                        (
                            team_positions
                            <= 4
                        ).mean()
                        * 100.0
                    ),
                    2,
                ),
                "top6_probability_pct": round(
                    float(
                        (
                            team_positions
                            <= 6
                        ).mean()
                        * 100.0
                    ),
                    2,
                ),
                "relegation_probability_pct": round(
                    float(
                        (
                            team_positions
                            >= (
                                team_count
                                - 3
                            )
                        ).mean()
                        * 100.0
                    ),
                    2,
                ),
            }
        )

    result = pd.DataFrame(
        result_rows
    )

    result = result.sort_values(
        by=[
            "champion_probability",
            "expected_points",
            "average_position",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    ).reset_index(
        drop=True
    )

    validate_simulation_result(
        result
    )

    return result


# =============================================================================
# Validação
# =============================================================================


def validate_simulation_result(
    dataframe: pd.DataFrame,
) -> None:
    """Valida propriedades essenciais do resultado do Monte Carlo."""

    if dataframe.empty:
        raise ValueError(
            "Resultado da simulação vazio."
        )

    probability_columns = [
        "champion_probability",
        "top4_probability",
        "top6_probability",
        "relegation_probability",
    ]

    if dataframe[
        probability_columns
    ].isna().any().any():
        raise ValueError(
            "Existem probabilidades nulas no Monte Carlo."
        )

    if (
        dataframe[
            probability_columns
        ] < 0.0
    ).any().any():
        raise ValueError(
            "Existem probabilidades negativas no Monte Carlo."
        )

    if (
        dataframe[
            probability_columns
        ] > 1.0
    ).any().any():
        raise ValueError(
            "Existem probabilidades acima de 1 no Monte Carlo."
        )

    champion_sum = float(
        dataframe[
            "champion_probability"
        ].sum()
    )

    if not np.isclose(
        champion_sum,
        1.0,
        atol=1e-6,
    ):
        raise ValueError(
            "As probabilidades de título não somam 100%."
        )


# =============================================================================
# Persistência
# =============================================================================


def save_simulation(
    dataframe: pd.DataFrame,
    output_file: Path | None = None,
) -> Path:
    """Salva o resumo do Monte Carlo."""

    path = (
        output_file
        if output_file is not None
        else get_simulation_file()
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


def print_simulation_summary(
    dataframe: pd.DataFrame,
) -> None:
    """Imprime um resumo amigável das simulações."""

    print()
    print(
        "=" * 100
    )
    print(
        "[SUMMARY] Monte Carlo do Brasileirão"
    )
    print(
        "=" * 100
    )

    simulations = int(
        dataframe[
            "simulations"
        ].iloc[
            0
        ]
    )

    print(
        f"Simulações: {simulations:,}".replace(
            ",",
            ".",
        )
    )

    print()
    print(
        "Probabilidades de título:"
    )

    for row in dataframe.head(
        10
    ).itertuples(
        index=False
    ):
        print(
            f"  {row.team_name:<28} "
            f"Título {row.champion_probability_pct:6.2f}% | "
            f"G4 {row.top4_probability_pct:6.2f}% | "
            f"Top 6 {row.top6_probability_pct:6.2f}% | "
            f"Rebaix. {row.relegation_probability_pct:6.2f}% | "
            f"Pts esp. {row.expected_points:5.1f}"
        )

    print()
    print(
        "Maiores riscos de rebaixamento:"
    )

    relegation = dataframe.sort_values(
        by=[
            "relegation_probability",
            "average_position",
        ],
        ascending=[
            False,
            False,
        ],
    ).head(
        6
    )

    for row in relegation.itertuples(
        index=False
    ):
        print(
            f"  {row.team_name:<28} "
            f"{row.relegation_probability_pct:6.2f}%"
        )