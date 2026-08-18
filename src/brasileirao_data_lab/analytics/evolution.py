from __future__ import annotations

import pandas as pd

from brasileirao_data_lab.analytics.championship import (
    get_played_matches,
    get_team_stats,
    load_matches,
)


# =============================================================================
# Validações
# =============================================================================


def validate_round_number(
    round_number: int,
) -> None:
    """Valida um número de rodada."""

    if round_number < 1:
        raise ValueError(
            "A rodada deve ser maior ou igual a 1."
        )


def get_latest_played_round(
    matches: pd.DataFrame,
) -> int | None:
    """
    Retorna a rodada mais alta que possui
    pelo menos uma partida realizada.
    """

    played = get_played_matches(
        matches
    )

    if played.empty:
        return None

    if "round" not in played.columns:
        raise ValueError(
            "O dataset não possui a coluna 'round'."
        )

    rounds = pd.to_numeric(
        played["round"],
        errors="coerce",
    ).dropna()

    if rounds.empty:
        return None

    return int(
        rounds.max()
    )


# =============================================================================
# Classificação por rodada
# =============================================================================


def get_round_table(
    matches: pd.DataFrame,
    round_number: int,
) -> pd.DataFrame:
    """
    Reconstrói a classificação acumulada
    até determinada rodada.

    Exemplo:

    round_number=10

    considera partidas realizadas pertencentes
    às rodadas 1 até 10.
    """

    validate_round_number(
        round_number
    )

    if "round" not in matches.columns:
        raise ValueError(
            "O dataset não possui a coluna 'round'."
        )

    rounds = pd.to_numeric(
        matches["round"],
        errors="coerce",
    )

    selected_matches = matches[
        rounds <= round_number
    ].copy()

    if selected_matches.empty:
        return pd.DataFrame()

    return get_team_stats(
        selected_matches
    )


# =============================================================================
# Histórico completo
# =============================================================================


def get_position_history(
    matches: pd.DataFrame,
    max_round: int | None = None,
) -> pd.DataFrame:
    """
    Reconstrói a posição de cada clube
    rodada por rodada.

    Retorna uma linha por:

    rodada + clube
    """

    latest_round = get_latest_played_round(
        matches
    )

    if latest_round is None:
        return pd.DataFrame(
            columns=[
                "round",
                "team_id",
                "team",
                "position",
                "points",
                "matches",
                "wins",
                "draws",
                "losses",
                "goals_for",
                "goals_against",
                "goal_difference",
            ]
        )

    if max_round is not None:

        validate_round_number(
            max_round
        )

        final_round = min(
            max_round,
            latest_round,
        )

    else:
        final_round = latest_round

    history = []

    for round_number in range(
        1,
        final_round + 1,
    ):

        table = get_round_table(
            matches,
            round_number,
        )

        if table.empty:
            continue

        for _, team in table.iterrows():

            history.append(
                {
                    "round": round_number,
                    "team_id": int(
                        team["team_id"]
                    ),
                    "team": team["team"],
                    "position": int(
                        team[
                            "calculated_position"
                        ]
                    ),
                    "points": int(
                        team["points"]
                    ),
                    "matches": int(
                        team["matches"]
                    ),
                    "wins": int(
                        team["wins"]
                    ),
                    "draws": int(
                        team["draws"]
                    ),
                    "losses": int(
                        team["losses"]
                    ),
                    "goals_for": int(
                        team["goals_for"]
                    ),
                    "goals_against": int(
                        team["goals_against"]
                    ),
                    "goal_difference": int(
                        team[
                            "goal_difference"
                        ]
                    ),
                }
            )

    dataframe = pd.DataFrame(
        history
    )

    if dataframe.empty:
        return dataframe

    return (
        dataframe.sort_values(
            by=[
                "round",
                "position",
            ]
        )
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Histórico de um clube
# =============================================================================


def get_team_position_history(
    matches: pd.DataFrame,
    team_id: int,
    max_round: int | None = None,
) -> pd.DataFrame:
    """
    Retorna a evolução de um único clube.
    """

    history = get_position_history(
        matches,
        max_round=max_round,
    )

    if history.empty:
        return history

    team_history = history[
        history["team_id"] == team_id
    ].copy()

    return (
        team_history.sort_values(
            "round"
        )
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Liderança
# =============================================================================


def get_round_leaders(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Retorna o líder calculado de cada rodada.
    """

    history = get_position_history(
        matches
    )

    if history.empty:
        return history

    leaders = history[
        history["position"] == 1
    ].copy()

    return (
        leaders.sort_values(
            "round"
        )
        .reset_index(
            drop=True
        )
    )


def get_leader_changes(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Retorna somente as rodadas em que
    houve troca de líder.

    A primeira rodada também é retornada,
    pois representa o primeiro líder.
    """

    leaders = get_round_leaders(
        matches
    )

    if leaders.empty:
        return leaders

    leaders = leaders.copy()

    leaders[
        "previous_leader_id"
    ] = leaders[
        "team_id"
    ].shift(1)

    changes = leaders[
        leaders["previous_leader_id"].isna()
        |
        (
            leaders["team_id"]
            != leaders["previous_leader_id"]
        )
    ].copy()

    return changes.reset_index(
        drop=True
    )


# =============================================================================
# Movimento de posições
# =============================================================================


def get_latest_position_changes(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compara a classificação da rodada mais
    avançada com a rodada anterior.

    position_change:

    positivo  = subiu posições
    zero      = permaneceu
    negativo  = caiu posições
    """

    latest_round = get_latest_played_round(
        matches
    )

    if (
        latest_round is None
        or latest_round <= 1
    ):
        return pd.DataFrame()

    current = get_round_table(
        matches,
        latest_round,
    )

    previous = get_round_table(
        matches,
        latest_round - 1,
    )

    if current.empty or previous.empty:
        return pd.DataFrame()

    current_data = current[
        [
            "team_id",
            "team",
            "calculated_position",
            "points",
        ]
    ].rename(
        columns={
            "calculated_position": (
                "current_position"
            ),
            "points": "current_points",
        }
    )

    previous_data = previous[
        [
            "team_id",
            "calculated_position",
            "points",
        ]
    ].rename(
        columns={
            "calculated_position": (
                "previous_position"
            ),
            "points": "previous_points",
        }
    )

    comparison = current_data.merge(
        previous_data,
        on="team_id",
        how="left",
        validate="one_to_one",
    )

    comparison[
        "position_change"
    ] = (
        comparison["previous_position"]
        - comparison["current_position"]
    )

    comparison[
        "points_gained"
    ] = (
        comparison["current_points"]
        - comparison["previous_points"]
    )

    comparison["round"] = (
        latest_round
    )

    comparison = comparison[
        [
            "round",
            "team_id",
            "team",
            "previous_position",
            "current_position",
            "position_change",
            "previous_points",
            "current_points",
            "points_gained",
        ]
    ]

    return (
        comparison.sort_values(
            by=[
                "position_change",
                "current_position",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Resumo no terminal
# =============================================================================


def print_evolution_summary() -> None:
    """
    Exibe um resumo da evolução da classificação.
    """

    matches = load_matches()

    latest_round = (
        get_latest_played_round(
            matches
        )
    )

    print()
    print("⚽ Brasileirão Data Lab")
    print("📈 V0.2 - Evolução do Campeonato")
    print("=" * 70)

    if latest_round is None:

        print()
        print(
            "Nenhuma partida realizada "
            "foi encontrada."
        )

        print()
        print("=" * 70)

        return

    current_table = get_round_table(
        matches,
        latest_round,
    )

    leader_changes = get_leader_changes(
        matches
    )

    position_changes = (
        get_latest_position_changes(
            matches
        )
    )

    # -------------------------------------------------------------------------
    # Situação atual
    # -------------------------------------------------------------------------

    print()
    print("SITUAÇÃO ATUAL")
    print("-" * 70)

    print(
        f"Rodada mais avançada com resultados: "
        f"{latest_round}"
    )

    if not current_table.empty:

        leader = current_table.iloc[0]

        print(
            f"Líder calculado: "
            f"{leader['team']} "
            f"({int(leader['points'])} pts)"
        )

    # -------------------------------------------------------------------------
    # Trocas de liderança
    # -------------------------------------------------------------------------

    print()
    print("👑 HISTÓRICO DE LIDERANÇA")
    print("-" * 70)

    if leader_changes.empty:

        print(
            "Nenhuma informação disponível."
        )

    else:

        for _, leader in (
            leader_changes.iterrows()
        ):

            print(
                f"Rodada "
                f"{int(leader['round']):>2}: "
                f"{leader['team']:<26} "
                f"{int(leader['points']):>3} pts"
            )

    # -------------------------------------------------------------------------
    # Movimento
    # -------------------------------------------------------------------------

    if not position_changes.empty:

        rises = (
            position_changes[
                position_changes[
                    "position_change"
                ] > 0
            ]
            .sort_values(
                by=[
                    "position_change",
                    "current_position",
                ],
                ascending=[
                    False,
                    True,
                ],
            )
        )

        falls = (
            position_changes[
                position_changes[
                    "position_change"
                ] < 0
            ]
            .sort_values(
                by=[
                    "position_change",
                    "current_position",
                ],
                ascending=[
                    True,
                    True,
                ],
            )
        )

        print()
        print(
            f"🚀 MAIORES ALTAS NA RODADA "
            f"{latest_round}"
        )
        print("-" * 70)

        if rises.empty:

            print(
                "Nenhum clube subiu de posição."
            )

        else:

            for _, team in (
                rises.head(5).iterrows()
            ):

                print(
                    f"{team['team']:<26} "
                    f"{int(team['previous_position']):>2}º "
                    f"→ "
                    f"{int(team['current_position']):>2}º "
                    f"(+{int(team['position_change'])})"
                )

        print()
        print(
            f"📉 MAIORES QUEDAS NA RODADA "
            f"{latest_round}"
        )
        print("-" * 70)

        if falls.empty:

            print(
                "Nenhum clube caiu de posição."
            )

        else:

            for _, team in (
                falls.head(5).iterrows()
            ):

                print(
                    f"{team['team']:<26} "
                    f"{int(team['previous_position']):>2}º "
                    f"→ "
                    f"{int(team['current_position']):>2}º "
                    f"({int(team['position_change'])})"
                )

    # -------------------------------------------------------------------------
    # Nota metodológica
    # -------------------------------------------------------------------------

    print()
    print("NOTA")
    print("-" * 70)

    print(
        "A evolução utiliza o número nominal das rodadas "
        "e os resultados atualmente disponíveis."
    )

    print(
        "Partidas adiadas podem alterar retrospectivamente "
        "a reconstrução de rodadas anteriores."
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    print_evolution_summary()
