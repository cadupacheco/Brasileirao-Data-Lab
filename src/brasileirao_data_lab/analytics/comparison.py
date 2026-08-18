from __future__ import annotations

import argparse
import unicodedata
from typing import Any

import pandas as pd

from brasileirao_data_lab.analytics.championship import (
    get_played_matches,
    get_recent_form_table,
    get_team_stats,
    load_matches,
    sort_matches_chronologically,
)


# =============================================================================
# Normalização de nomes
# =============================================================================


def normalize_team_name(
    value: str,
) -> str:
    """
    Normaliza o nome de um clube para facilitar buscas.

    Remove:
    - diferenças entre maiúsculas/minúsculas
    - acentos
    - espaços extras
    """

    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    return " ".join(
        normalized.casefold().split()
    )


# =============================================================================
# Clubes disponíveis
# =============================================================================


def get_available_teams(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna os clubes únicos disponíveis no dataset."""

    home = matches[
        [
            "home_team_id",
            "home_team",
        ]
    ].rename(
        columns={
            "home_team_id": "team_id",
            "home_team": "team",
        }
    )

    away = matches[
        [
            "away_team_id",
            "away_team",
        ]
    ].rename(
        columns={
            "away_team_id": "team_id",
            "away_team": "team",
        }
    )

    teams = pd.concat(
        [
            home,
            away,
        ],
        ignore_index=True,
    )

    teams = (
        teams.dropna(
            subset=[
                "team_id",
                "team",
            ]
        )
        .drop_duplicates(
            subset=["team_id"]
        )
        .sort_values(
            "team"
        )
        .reset_index(
            drop=True
        )
    )

    teams["team_id"] = (
        teams["team_id"]
        .astype(int)
    )

    return teams


# =============================================================================
# Resolução de clube
# =============================================================================


def resolve_team(
    matches: pd.DataFrame,
    identifier: int | str,
) -> dict[str, Any]:
    """
    Localiza um clube pelo ID ou pelo nome.

    Exemplos:

    20001
    "20001"
    "Corinthians"
    "atletico mineiro"
    """

    teams = get_available_teams(
        matches
    )

    # -------------------------------------------------------------------------
    # ID numérico
    # -------------------------------------------------------------------------

    if isinstance(
        identifier,
        int,
    ):

        result = teams[
            teams["team_id"] == identifier
        ]

        if result.empty:
            raise ValueError(
                f"Clube com ID "
                f"{identifier} não encontrado."
            )

        row = result.iloc[0]

        return {
            "team_id": int(
                row["team_id"]
            ),
            "team": row["team"],
        }

    text = str(
        identifier
    ).strip()

    if text.isdigit():

        return resolve_team(
            matches,
            int(text),
        )

    # -------------------------------------------------------------------------
    # Nome
    # -------------------------------------------------------------------------

    normalized_search = (
        normalize_team_name(
            text
        )
    )

    normalized_names = (
        teams["team"]
        .astype(str)
        .map(
            normalize_team_name
        )
    )

    # Primeiro tenta correspondência exata.

    exact = teams[
        normalized_names
        == normalized_search
    ]

    if len(exact) == 1:

        row = exact.iloc[0]

        return {
            "team_id": int(
                row["team_id"]
            ),
            "team": row["team"],
        }

    # Depois permite uma busca parcial,
    # desde que exista apenas um resultado.

    partial_mask = (
        normalized_names.str.contains(
            normalized_search,
            regex=False,
        )
    )

    partial = teams[
        partial_mask
    ]

    if len(partial) == 1:

        row = partial.iloc[0]

        return {
            "team_id": int(
                row["team_id"]
            ),
            "team": row["team"],
        }

    if len(partial) > 1:

        names = ", ".join(
            partial["team"].tolist()
        )

        raise ValueError(
            f"Busca ambígua para "
            f"{identifier!r}. "
            f"Clubes encontrados: {names}"
        )

    raise ValueError(
        f"Clube {identifier!r} "
        f"não encontrado."
    )


# =============================================================================
# Perfil do clube
# =============================================================================


def get_team_profile(
    matches: pd.DataFrame,
    team_id: int,
    recent_n: int = 5,
) -> dict[str, Any]:
    """
    Retorna as principais métricas de um clube.
    """

    if recent_n <= 0:
        raise ValueError(
            "recent_n deve ser maior que zero."
        )

    standings = get_team_stats(
        matches
    )

    recent_form = get_recent_form_table(
        matches,
        last_n=recent_n,
    )

    team_data = standings[
        standings["team_id"] == team_id
    ]

    if team_data.empty:

        raise ValueError(
            f"Clube com ID "
            f"{team_id} não encontrado."
        )

    team = team_data.iloc[0]

    recent_data = recent_form[
        recent_form["team_id"] == team_id
    ]

    if recent_data.empty:

        recent = {
            "recent_matches": 0,
            "recent_wins": 0,
            "recent_draws": 0,
            "recent_losses": 0,
            "recent_points": 0,
            "recent_goals_for": 0,
            "recent_goals_against": 0,
            "recent_goal_difference": 0,
            "recent_performance_pct": 0.0,
            "recent_form": "",
        }

    else:

        recent_row = (
            recent_data.iloc[0]
        )

        recent = {
            "recent_matches": int(
                recent_row[
                    "recent_matches"
                ]
            ),
            "recent_wins": int(
                recent_row[
                    "recent_wins"
                ]
            ),
            "recent_draws": int(
                recent_row[
                    "recent_draws"
                ]
            ),
            "recent_losses": int(
                recent_row[
                    "recent_losses"
                ]
            ),
            "recent_points": int(
                recent_row[
                    "recent_points"
                ]
            ),
            "recent_goals_for": int(
                recent_row[
                    "recent_goals_for"
                ]
            ),
            "recent_goals_against": int(
                recent_row[
                    "recent_goals_against"
                ]
            ),
            "recent_goal_difference": int(
                recent_row[
                    "recent_goal_difference"
                ]
            ),
            "recent_performance_pct": float(
                recent_row[
                    "recent_performance_pct"
                ]
            ),
            "recent_form": recent_row[
                "recent_form"
            ],
        }

    profile = {
        "team_id": int(
            team["team_id"]
        ),
        "team": team["team"],
        "position": int(
            team[
                "calculated_position"
            ]
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
        "points": int(
            team["points"]
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
        "performance_pct": float(
            team[
                "performance_pct"
            ]
        ),
        "home_matches": int(
            team[
                "home_matches"
            ]
        ),
        "home_wins": int(
            team[
                "home_wins"
            ]
        ),
        "home_draws": int(
            team[
                "home_draws"
            ]
        ),
        "home_losses": int(
            team[
                "home_losses"
            ]
        ),
        "home_points": int(
            team[
                "home_points"
            ]
        ),
        "home_performance_pct": float(
            team[
                "home_performance_pct"
            ]
        ),
        "away_matches": int(
            team[
                "away_matches"
            ]
        ),
        "away_wins": int(
            team[
                "away_wins"
            ]
        ),
        "away_draws": int(
            team[
                "away_draws"
            ]
        ),
        "away_losses": int(
            team[
                "away_losses"
            ]
        ),
        "away_points": int(
            team[
                "away_points"
            ]
        ),
        "away_performance_pct": float(
            team[
                "away_performance_pct"
            ]
        ),
    }

    profile.update(
        recent
    )

    return profile


# =============================================================================
# Confronto direto
# =============================================================================


def get_head_to_head(
    matches: pd.DataFrame,
    team_a_id: int,
    team_b_id: int,
) -> dict[str, Any]:
    """
    Calcula o confronto direto entre dois clubes
    utilizando somente partidas realizadas.
    """

    if team_a_id == team_b_id:
        raise ValueError(
            "Os clubes da comparação "
            "devem ser diferentes."
        )

    played = get_played_matches(
        matches
    )

    direct_matches = played[
        (
            (
                played["home_team_id"]
                == team_a_id
            )
            &
            (
                played["away_team_id"]
                == team_b_id
            )
        )
        |
        (
            (
                played["home_team_id"]
                == team_b_id
            )
            &
            (
                played["away_team_id"]
                == team_a_id
            )
        )
    ].copy()

    if not direct_matches.empty:

        direct_matches = (
            sort_matches_chronologically(
                direct_matches
            )
        )

    team_a_wins = 0
    team_b_wins = 0
    draws = 0

    team_a_goals = 0
    team_b_goals = 0

    games = []

    for _, match in (
        direct_matches.iterrows()
    ):

        team_a_is_home = (
            int(
                match["home_team_id"]
            )
            == team_a_id
        )

        if team_a_is_home:

            team_a_score = int(
                match[
                    "home_goals"
                ]
            )

            team_b_score = int(
                match[
                    "away_goals"
                ]
            )

        else:

            team_a_score = int(
                match[
                    "away_goals"
                ]
            )

            team_b_score = int(
                match[
                    "home_goals"
                ]
            )

        team_a_goals += (
            team_a_score
        )

        team_b_goals += (
            team_b_score
        )

        if (
            team_a_score
            > team_b_score
        ):
            team_a_wins += 1

        elif (
            team_b_score
            > team_a_score
        ):
            team_b_wins += 1

        else:
            draws += 1

        games.append(
            {
                "match_id": (
                    int(
                        match["match_id"]
                    )
                    if (
                        "match_id"
                        in match
                        and pd.notna(
                            match[
                                "match_id"
                            ]
                        )
                    )
                    else None
                ),
                "round": (
                    int(
                        match["round"]
                    )
                    if (
                        "round"
                        in match
                        and pd.notna(
                            match["round"]
                        )
                    )
                    else None
                ),
                "date": (
                    match["date"]
                    if "date" in match
                    else None
                ),
                "home_team": (
                    match[
                        "home_team"
                    ]
                ),
                "away_team": (
                    match[
                        "away_team"
                    ]
                ),
                "home_goals": int(
                    match[
                        "home_goals"
                    ]
                ),
                "away_goals": int(
                    match[
                        "away_goals"
                    ]
                ),
            }
        )

    return {
        "matches": len(
            direct_matches
        ),
        "team_a_wins": team_a_wins,
        "team_b_wins": team_b_wins,
        "draws": draws,
        "team_a_goals": team_a_goals,
        "team_b_goals": team_b_goals,
        "games": games,
    }


# =============================================================================
# Comparação de métricas
# =============================================================================


def get_metric_winner(
    team_a: dict[str, Any],
    team_b: dict[str, Any],
    metric: str,
    lower_is_better: bool = False,
) -> int | None:
    """
    Retorna o team_id vencedor em determinada métrica.

    None significa empate.
    """

    value_a = team_a[
        metric
    ]

    value_b = team_b[
        metric
    ]

    if value_a == value_b:
        return None

    if lower_is_better:

        return (
            team_a["team_id"]
            if value_a < value_b
            else team_b["team_id"]
        )

    return (
        team_a["team_id"]
        if value_a > value_b
        else team_b["team_id"]
    )


def compare_teams(
    matches: pd.DataFrame,
    team_a_id: int,
    team_b_id: int,
    recent_n: int = 5,
) -> dict[str, Any]:
    """
    Compara dois clubes em várias métricas.
    """

    if team_a_id == team_b_id:
        raise ValueError(
            "Os clubes da comparação "
            "devem ser diferentes."
        )

    team_a = get_team_profile(
        matches,
        team_a_id,
        recent_n=recent_n,
    )

    team_b = get_team_profile(
        matches,
        team_b_id,
        recent_n=recent_n,
    )

    head_to_head = get_head_to_head(
        matches,
        team_a_id,
        team_b_id,
    )

    metric_rules = {
        "position": True,
        "points": False,
        "wins": False,
        "goals_for": False,
        "goals_against": True,
        "goal_difference": False,
        "performance_pct": False,
        "home_performance_pct": False,
        "away_performance_pct": False,
        "recent_points": False,
        "recent_goal_difference": False,
    }

    winners = {}

    for metric, lower_is_better in (
        metric_rules.items()
    ):

        winners[metric] = (
            get_metric_winner(
                team_a,
                team_b,
                metric,
                lower_is_better=(
                    lower_is_better
                ),
            )
        )

    advantages = {
        team_a_id: 0,
        team_b_id: 0,
    }

    for winner in (
        winners.values()
    ):

        if winner is not None:

            advantages[
                winner
            ] += 1

    if (
        advantages[team_a_id]
        > advantages[team_b_id]
    ):
        overall_advantage = (
            team_a_id
        )

    elif (
        advantages[team_b_id]
        > advantages[team_a_id]
    ):
        overall_advantage = (
            team_b_id
        )

    else:
        overall_advantage = None

    return {
        "team_a": team_a,
        "team_b": team_b,
        "metric_winners": winners,
        "advantages": advantages,
        "overall_advantage": (
            overall_advantage
        ),
        "head_to_head": head_to_head,
    }


# =============================================================================
# Formatação
# =============================================================================


def format_goal_difference(
    value: int,
) -> str:
    """Formata saldo de gols."""

    if value > 0:
        return f"+{value}"

    return str(
        value
    )


def format_form(
    value: str,
) -> str:
    """Formata a sequência recente."""

    if not value:
        return "-"

    return value


# =============================================================================
# Terminal
# =============================================================================


def print_team_comparison(
    team_a_identifier: int | str | None = None,
    team_b_identifier: int | str | None = None,
) -> None:
    """
    Exibe uma comparação entre dois clubes.

    Se nenhum clube for informado,
    compara os dois primeiros da classificação.
    """

    matches = load_matches()

    standings = get_team_stats(
        matches
    )

    if standings.empty:
        raise ValueError(
            "Não existem partidas "
            "realizadas para comparação."
        )

    # -------------------------------------------------------------------------
    # Define os clubes
    # -------------------------------------------------------------------------

    if (
        team_a_identifier is None
        and team_b_identifier is None
    ):

        team_a_id = int(
            standings.iloc[0][
                "team_id"
            ]
        )

        team_b_id = int(
            standings.iloc[1][
                "team_id"
            ]
        )

    elif (
        team_a_identifier is None
        or team_b_identifier is None
    ):

        raise ValueError(
            "Informe dois clubes "
            "ou nenhum clube."
        )

    else:

        team_a_id = (
            resolve_team(
                matches,
                team_a_identifier,
            )["team_id"]
        )

        team_b_id = (
            resolve_team(
                matches,
                team_b_identifier,
            )["team_id"]
        )

    comparison = compare_teams(
        matches,
        team_a_id,
        team_b_id,
        recent_n=5,
    )

    team_a = comparison[
        "team_a"
    ]

    team_b = comparison[
        "team_b"
    ]

    h2h = comparison[
        "head_to_head"
    ]

    # -------------------------------------------------------------------------
    # Cabeçalho
    # -------------------------------------------------------------------------

    print()
    print("⚽ Brasileirão Data Lab")
    print("⚔️ V0.2 - Comparação entre Clubes")
    print("=" * 76)

    print()
    print(
        f"{team_a['team']}"
        f"  ⚔️  "
        f"{team_b['team']}"
    )

    print()

    print(
        f"{'MÉTRICA':<28}"
        f"{team_a['team'][:20]:>22}"
        f"{team_b['team'][:20]:>22}"
    )

    print("-" * 76)

    # -------------------------------------------------------------------------
    # Geral
    # -------------------------------------------------------------------------

    rows = [
        (
            "Posição",
            f"{team_a['position']}º",
            f"{team_b['position']}º",
        ),
        (
            "Pontos",
            team_a["points"],
            team_b["points"],
        ),
        (
            "Jogos",
            team_a["matches"],
            team_b["matches"],
        ),
        (
            "Vitórias",
            team_a["wins"],
            team_b["wins"],
        ),
        (
            "Empates",
            team_a["draws"],
            team_b["draws"],
        ),
        (
            "Derrotas",
            team_a["losses"],
            team_b["losses"],
        ),
        (
            "Gols marcados",
            team_a["goals_for"],
            team_b["goals_for"],
        ),
        (
            "Gols sofridos",
            team_a[
                "goals_against"
            ],
            team_b[
                "goals_against"
            ],
        ),
        (
            "Saldo de gols",
            format_goal_difference(
                team_a[
                    "goal_difference"
                ]
            ),
            format_goal_difference(
                team_b[
                    "goal_difference"
                ]
            ),
        ),
        (
            "Aproveitamento",
            (
                f"{team_a['performance_pct']:.2f}%"
            ),
            (
                f"{team_b['performance_pct']:.2f}%"
            ),
        ),
        (
            "🏠 Aproveitamento casa",
            (
                f"{team_a['home_performance_pct']:.2f}%"
            ),
            (
                f"{team_b['home_performance_pct']:.2f}%"
            ),
        ),
        (
            "✈️ Aproveitamento fora",
            (
                f"{team_a['away_performance_pct']:.2f}%"
            ),
            (
                f"{team_b['away_performance_pct']:.2f}%"
            ),
        ),
        (
            "🔥 Pontos últimos 5",
            (
                f"{team_a['recent_points']}/15"
            ),
            (
                f"{team_b['recent_points']}/15"
            ),
        ),
        (
            "🔥 Forma últimos 5",
            format_form(
                team_a[
                    "recent_form"
                ]
            ),
            format_form(
                team_b[
                    "recent_form"
                ]
            ),
        ),
    ]

    for (
        label,
        value_a,
        value_b,
    ) in rows:

        print(
            f"{label:<28}"
            f"{str(value_a):>22}"
            f"{str(value_b):>22}"
        )

    # -------------------------------------------------------------------------
    # Vantagem geral
    # -------------------------------------------------------------------------

    print()
    print("📊 COMPARAÇÃO DE MÉTRICAS")
    print("-" * 76)

    advantage_a = (
        comparison[
            "advantages"
        ][team_a_id]
    )

    advantage_b = (
        comparison[
            "advantages"
        ][team_b_id]
    )

    print(
        f"Métricas favoráveis a "
        f"{team_a['team']}: "
        f"{advantage_a}"
    )

    print(
        f"Métricas favoráveis a "
        f"{team_b['team']}: "
        f"{advantage_b}"
    )

    overall = comparison[
        "overall_advantage"
    ]

    if overall is None:

        print(
            "Resultado comparativo: "
            "equilíbrio."
        )

    elif overall == team_a_id:

        print(
            f"Vantagem geral: "
            f"{team_a['team']} ✅"
        )

    else:

        print(
            f"Vantagem geral: "
            f"{team_b['team']} ✅"
        )

    # -------------------------------------------------------------------------
    # Confronto direto
    # -------------------------------------------------------------------------

    print()
    print("⚔️ CONFRONTO DIRETO NA TEMPORADA")
    print("-" * 76)

    print(
        f"Jogos realizados: "
        f"{h2h['matches']}"
    )

    print(
        f"Vitórias {team_a['team']}: "
        f"{h2h['team_a_wins']}"
    )

    print(
        f"Empates: "
        f"{h2h['draws']}"
    )

    print(
        f"Vitórias {team_b['team']}: "
        f"{h2h['team_b_wins']}"
    )

    print(
        f"Gols no confronto: "
        f"{team_a['team']} "
        f"{h2h['team_a_goals']} x "
        f"{h2h['team_b_goals']} "
        f"{team_b['team']}"
    )

    if h2h["games"]:

        print()
        print("Partidas:")

        for game in h2h[
            "games"
        ]:

            round_text = (
                f"R{game['round']}"
                if (
                    game["round"]
                    is not None
                )
                else "Rodada ?"
            )

            print(
                f"  {round_text:<5} "
                f"{game['home_team']} "
                f"{game['home_goals']} x "
                f"{game['away_goals']} "
                f"{game['away_team']}"
            )

    print()
    print("=" * 76)


# =============================================================================
# CLI
# =============================================================================


def main() -> None:
    """Entrada do módulo via terminal."""

    parser = argparse.ArgumentParser(
        description=(
            "Compara dois clubes do "
            "Brasileirão Data Lab."
        )
    )

    parser.add_argument(
        "team_a",
        nargs="?",
        help=(
            "Nome ou ID do primeiro clube."
        ),
    )

    parser.add_argument(
        "team_b",
        nargs="?",
        help=(
            "Nome ou ID do segundo clube."
        ),
    )

    args = parser.parse_args()

    if (
        (args.team_a is None)
        != (args.team_b is None)
    ):

        parser.error(
            "Informe os dois clubes "
            "ou nenhum."
        )

    print_team_comparison(
        args.team_a,
        args.team_b,
    )


if __name__ == "__main__":
    main()