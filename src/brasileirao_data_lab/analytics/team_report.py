from __future__ import annotations

import argparse
from typing import Any

import pandas as pd

from brasileirao_data_lab.analytics.championship import (
    get_future_matches,
    get_team_recent_matches,
    get_team_stats,
    load_matches,
)
from brasileirao_data_lab.analytics.comparison import (
    get_team_profile,
    resolve_team,
)
from brasileirao_data_lab.analytics.evolution import (
    get_latest_played_round,
    get_team_position_history,
)


# =============================================================================
# Jogos futuros
# =============================================================================


def get_team_future_matches(
    matches: pd.DataFrame,
    team_id: int,
) -> pd.DataFrame:
    """
    Retorna todos os jogos ainda sem placar de um clube.

    A ordenação prioriza partidas que já possuem
    data definida.

    Ordem:
    1. jogos com data definida
    2. data
    3. horário
    4. rodada
    5. número da partida

    Jogos ainda sem data ficam no final.
    """

    future = get_future_matches(
        matches
    )

    team_matches = future[
        (
            future["home_team_id"] == team_id
        )
        |
        (
            future["away_team_id"] == team_id
        )
    ].copy()

    if team_matches.empty:
        return team_matches

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    if "date" in team_matches.columns:

        team_matches["_date_sort"] = pd.to_datetime(
            team_matches["date"],
            errors="coerce",
        )

    else:

        team_matches["_date_sort"] = pd.NaT

    team_matches["_has_defined_date"] = (
        team_matches[
            "_date_sort"
        ].notna()
    )

    # -------------------------------------------------------------------------
    # Horário
    # -------------------------------------------------------------------------

    if "time" in team_matches.columns:

        team_matches["_time_sort"] = (
            team_matches["time"]
            .fillna("")
            .astype(str)
        )

    else:

        team_matches["_time_sort"] = ""

    # -------------------------------------------------------------------------
    # Rodada
    # -------------------------------------------------------------------------

    if "round" in team_matches.columns:

        team_matches["_round_sort"] = pd.to_numeric(
            team_matches["round"],
            errors="coerce",
        )

    else:

        team_matches["_round_sort"] = None

    # -------------------------------------------------------------------------
    # Número da partida
    # -------------------------------------------------------------------------

    if "match_number" in team_matches.columns:

        team_matches[
            "_match_number_sort"
        ] = pd.to_numeric(
            team_matches[
                "match_number"
            ],
            errors="coerce",
        )

    else:

        team_matches[
            "_match_number_sort"
        ] = None

    # -------------------------------------------------------------------------
    # Ordenação
    # -------------------------------------------------------------------------

    team_matches = (
        team_matches.sort_values(
            by=[
                "_has_defined_date",
                "_date_sort",
                "_time_sort",
                "_round_sort",
                "_match_number_sort",
            ],
            ascending=[
                False,
                True,
                True,
                True,
                True,
            ],
            na_position="last",
        )
        .drop(
            columns=[
                "_has_defined_date",
                "_date_sort",
                "_time_sort",
                "_round_sort",
                "_match_number_sort",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return team_matches


def get_team_unscheduled_matches(
    matches: pd.DataFrame,
    team_id: int,
) -> pd.DataFrame:
    """
    Retorna todos os jogos sem placar
    que ainda não possuem data definida.
    """

    future = get_future_matches(
        matches
    )

    team_matches = future[
        (
            future["home_team_id"] == team_id
        )
        |
        (
            future["away_team_id"] == team_id
        )
    ].copy()

    if team_matches.empty:
        return team_matches

    if "date" not in team_matches.columns:
        return team_matches

    parsed_dates = pd.to_datetime(
        team_matches["date"],
        errors="coerce",
    )

    unscheduled = team_matches[
        parsed_dates.isna()
    ].copy()

    if unscheduled.empty:
        return unscheduled

    if "round" in unscheduled.columns:

        unscheduled["_round_sort"] = pd.to_numeric(
            unscheduled["round"],
            errors="coerce",
        )

    else:

        unscheduled["_round_sort"] = None

    if "match_number" in unscheduled.columns:

        unscheduled[
            "_match_number_sort"
        ] = pd.to_numeric(
            unscheduled[
                "match_number"
            ],
            errors="coerce",
        )

    else:

        unscheduled[
            "_match_number_sort"
        ] = None

    unscheduled = (
        unscheduled.sort_values(
            by=[
                "_round_sort",
                "_match_number_sort",
            ],
            na_position="last",
        )
        .drop(
            columns=[
                "_round_sort",
                "_match_number_sort",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return unscheduled


# =============================================================================
# Classificação de jogos sem data
# =============================================================================


def get_team_overdue_unscheduled_matches(
    matches: pd.DataFrame,
    team_id: int,
) -> pd.DataFrame:
    """
    Retorna jogos sem data pertencentes a rodadas
    iguais ou anteriores à rodada mais avançada
    que já possui resultados.

    Esses jogos representam pendências do calendário
    até o estágio atual do campeonato.
    """

    unscheduled = get_team_unscheduled_matches(
        matches,
        team_id,
    )

    if unscheduled.empty:
        return unscheduled

    latest_round = get_latest_played_round(
        matches
    )

    if latest_round is None:
        return unscheduled.iloc[0:0].copy()

    if "round" not in unscheduled.columns:
        return unscheduled.iloc[0:0].copy()

    rounds = pd.to_numeric(
        unscheduled["round"],
        errors="coerce",
    )

    overdue = unscheduled[
        rounds <= latest_round
    ].copy()

    return overdue.reset_index(
        drop=True
    )


def get_team_upcoming_unscheduled_matches(
    matches: pd.DataFrame,
    team_id: int,
) -> pd.DataFrame:
    """
    Retorna jogos de rodadas futuras
    que ainda não possuem data definida.
    """

    unscheduled = get_team_unscheduled_matches(
        matches,
        team_id,
    )

    if unscheduled.empty:
        return unscheduled

    latest_round = get_latest_played_round(
        matches
    )

    if latest_round is None:
        return unscheduled.reset_index(
            drop=True
        )

    if "round" not in unscheduled.columns:
        return unscheduled.reset_index(
            drop=True
        )

    rounds = pd.to_numeric(
        unscheduled["round"],
        errors="coerce",
    )

    upcoming = unscheduled[
        rounds.isna()
        |
        (
            rounds > latest_round
        )
    ].copy()

    return upcoming.reset_index(
        drop=True
    )


# =============================================================================
# Perspectiva do clube
# =============================================================================


def match_to_team_perspective(
    match: pd.Series,
    team_id: int,
) -> dict[str, Any]:
    """
    Converte uma partida para a perspectiva
    do clube informado.
    """

    is_home = (
        int(
            match["home_team_id"]
        )
        == int(team_id)
    )

    if is_home:

        opponent_id = int(
            match["away_team_id"]
        )

        opponent = match[
            "away_team"
        ]

    else:

        opponent_id = int(
            match["home_team_id"]
        )

        opponent = match[
            "home_team"
        ]

    return {
        "match_id": (
            int(
                match["match_id"]
            )
            if (
                "match_id" in match
                and pd.notna(
                    match["match_id"]
                )
            )
            else None
        ),
        "round": (
            int(
                match["round"]
            )
            if (
                "round" in match
                and pd.notna(
                    match["round"]
                )
            )
            else None
        ),
        "date": (
            match["date"]
            if (
                "date" in match
                and pd.notna(
                    match["date"]
                )
            )
            else None
        ),
        "time": (
            match["time"]
            if (
                "time" in match
                and pd.notna(
                    match["time"]
                )
            )
            else None
        ),
        "home": is_home,
        "opponent_id": opponent_id,
        "opponent": opponent,
        "venue": (
            match["venue"]
            if (
                "venue" in match
                and pd.notna(
                    match["venue"]
                )
            )
            else None
        ),
        "city": (
            match["city"]
            if (
                "city" in match
                and pd.notna(
                    match["city"]
                )
            )
            else None
        ),
        "state": (
            match["state"]
            if (
                "state" in match
                and pd.notna(
                    match["state"]
                )
            )
            else None
        ),
    }


def get_next_match(
    matches: pd.DataFrame,
    team_id: int,
) -> dict[str, Any] | None:
    """
    Retorna a próxima partida com data definida.

    Caso nenhuma partida possua data definida,
    retorna a primeira partida futura disponível.
    """

    future = get_team_future_matches(
        matches,
        team_id,
    )

    if future.empty:
        return None

    if "date" in future.columns:

        parsed_dates = pd.to_datetime(
            future["date"],
            errors="coerce",
        )

        scheduled = future[
            parsed_dates.notna()
        ]

        if not scheduled.empty:

            return match_to_team_perspective(
                scheduled.iloc[0],
                team_id,
            )

    return match_to_team_perspective(
        future.iloc[0],
        team_id,
    )


# =============================================================================
# Evolução do clube
# =============================================================================


def get_team_evolution_summary(
    matches: pd.DataFrame,
    team_id: int,
) -> dict[str, Any]:
    """
    Resume a evolução do clube no campeonato.
    """

    history = get_team_position_history(
        matches,
        team_id=team_id,
    )

    if history.empty:

        return {
            "best_position": None,
            "worst_position": None,
            "initial_position": None,
            "current_position": None,
            "position_change": None,
            "rounds_tracked": 0,
        }

    initial_position = int(
        history.iloc[0][
            "position"
        ]
    )

    current_position = int(
        history.iloc[-1][
            "position"
        ]
    )

    best_position = int(
        history["position"].min()
    )

    worst_position = int(
        history["position"].max()
    )

    return {
        "best_position": best_position,
        "worst_position": worst_position,
        "initial_position": initial_position,
        "current_position": current_position,
        "position_change": (
            initial_position
            - current_position
        ),
        "rounds_tracked": len(
            history
        ),
    }


# =============================================================================
# Médias
# =============================================================================


def get_team_averages(
    profile: dict[str, Any],
) -> dict[str, float]:
    """Calcula médias por partida."""

    matches_played = profile[
        "matches"
    ]

    if matches_played == 0:

        return {
            "goals_for_per_match": 0.0,
            "goals_against_per_match": 0.0,
            "points_per_match": 0.0,
        }

    return {
        "goals_for_per_match": round(
            profile["goals_for"]
            / matches_played,
            2,
        ),
        "goals_against_per_match": round(
            profile["goals_against"]
            / matches_played,
            2,
        ),
        "points_per_match": round(
            profile["points"]
            / matches_played,
            2,
        ),
    }


# =============================================================================
# Relatório completo
# =============================================================================


def get_team_report(
    matches: pd.DataFrame,
    team_id: int,
    recent_n: int = 5,
) -> dict[str, Any]:
    """
    Monta o relatório completo de um clube.
    """

    if recent_n <= 0:
        raise ValueError(
            "recent_n deve ser maior que zero."
        )

    profile = get_team_profile(
        matches,
        team_id=team_id,
        recent_n=recent_n,
    )

    evolution = (
        get_team_evolution_summary(
            matches,
            team_id=team_id,
        )
    )

    recent_matches = (
        get_team_recent_matches(
            matches,
            team_id=team_id,
            last_n=recent_n,
        )
    )

    next_match = get_next_match(
        matches,
        team_id=team_id,
    )

    unscheduled_matches = (
        get_team_unscheduled_matches(
            matches,
            team_id=team_id,
        )
    )

    overdue_unscheduled_matches = (
        get_team_overdue_unscheduled_matches(
            matches,
            team_id=team_id,
        )
    )

    upcoming_unscheduled_matches = (
        get_team_upcoming_unscheduled_matches(
            matches,
            team_id=team_id,
        )
    )

    averages = get_team_averages(
        profile
    )

    return {
        "profile": profile,
        "evolution": evolution,
        "recent_matches": recent_matches,
        "next_match": next_match,
        "unscheduled_matches": unscheduled_matches,
        "overdue_unscheduled_matches": (
            overdue_unscheduled_matches
        ),
        "upcoming_unscheduled_matches": (
            upcoming_unscheduled_matches
        ),
        "averages": averages,
    }


# =============================================================================
# Formatação
# =============================================================================


def format_position(
    value: int | None,
) -> str:
    """Formata uma posição."""

    if value is None:
        return "-"

    return f"{value}º"


def format_percentage(
    value: float,
) -> str:
    """Formata percentual."""

    return f"{value:.2f}%"


def format_date(
    value: str | None,
) -> str:
    """Formata data para exibição."""

    if not value:
        return "A definir"

    parsed = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(parsed):
        return str(value)

    return parsed.strftime(
        "%d/%m/%Y"
    )


def format_time(
    value: str | None,
) -> str:
    """Formata horário."""

    if not value:
        return "A definir"

    return str(value)


def get_result_icon(
    result: str,
) -> str:
    """Retorna um símbolo para o resultado."""

    icons = {
        "V": "🟢",
        "E": "⚪",
        "D": "🔴",
    }

    return icons.get(
        result,
        "•",
    )


# =============================================================================
# Impressão de jogos sem data
# =============================================================================


def print_unscheduled_match(
    match: pd.Series,
    team_id: int,
    icon: str,
) -> None:
    """Imprime uma partida sem data."""

    perspective = (
        match_to_team_perspective(
            match,
            team_id,
        )
    )

    location = (
        "CASA"
        if perspective["home"]
        else "FORA"
    )

    round_text = (
        f"R{perspective['round']}"
        if (
            perspective["round"]
            is not None
        )
        else "R?"
    )

    print(
        f"  {icon} "
        f"{round_text:<4} "
        f"{location:<4} | "
        f"{perspective['opponent']}"
    )


# =============================================================================
# Terminal
# =============================================================================


def print_team_report(
    team_identifier: int | str | None = None,
) -> None:
    """
    Exibe o relatório individual de um clube.

    Sem argumento, utiliza o atual líder calculado.
    """

    matches = load_matches()

    if team_identifier is None:

        standings = get_team_stats(
            matches
        )

        if standings.empty:
            raise ValueError(
                "Não existem partidas realizadas."
            )

        team_id = int(
            standings.iloc[0][
                "team_id"
            ]
        )

    else:

        team = resolve_team(
            matches,
            team_identifier,
        )

        team_id = int(
            team["team_id"]
        )

    report = get_team_report(
        matches,
        team_id=team_id,
        recent_n=5,
    )

    profile = report[
        "profile"
    ]

    evolution = report[
        "evolution"
    ]

    averages = report[
        "averages"
    ]

    next_match = report[
        "next_match"
    ]

    recent_matches = report[
        "recent_matches"
    ]

    overdue_unscheduled_matches = report[
        "overdue_unscheduled_matches"
    ]

    upcoming_unscheduled_matches = report[
        "upcoming_unscheduled_matches"
    ]

    # -------------------------------------------------------------------------
    # Cabeçalho
    # -------------------------------------------------------------------------

    print()
    print("⚽ Brasileirão Data Lab")
    print("📋 V0.2 - Relatório do Clube")
    print("=" * 76)

    print()
    print(
        f"🏟️ {profile['team']}"
    )

    print(
        f"{profile['position']}º lugar | "
        f"{profile['points']} pontos | "
        f"{profile['matches']} jogos"
    )

    # -------------------------------------------------------------------------
    # Geral
    # -------------------------------------------------------------------------

    print()
    print("📊 DESEMPENHO GERAL")
    print("-" * 76)

    print(
        f"Vitórias: "
        f"{profile['wins']}"
    )

    print(
        f"Empates: "
        f"{profile['draws']}"
    )

    print(
        f"Derrotas: "
        f"{profile['losses']}"
    )

    print(
        f"Aproveitamento: "
        f"{format_percentage(profile['performance_pct'])}"
    )

    print(
        f"Pontos por jogo: "
        f"{averages['points_per_match']:.2f}"
    )

    # -------------------------------------------------------------------------
    # Gols
    # -------------------------------------------------------------------------

    print()
    print("⚽ GOLS")
    print("-" * 76)

    print(
        f"Marcados: "
        f"{profile['goals_for']}"
    )

    print(
        f"Sofridos: "
        f"{profile['goals_against']}"
    )

    print(
        f"Saldo: "
        f"{profile['goal_difference']:+d}"
    )

    print(
        f"Média marcados/jogo: "
        f"{averages['goals_for_per_match']:.2f}"
    )

    print(
        f"Média sofridos/jogo: "
        f"{averages['goals_against_per_match']:.2f}"
    )

    # -------------------------------------------------------------------------
    # Casa
    # -------------------------------------------------------------------------

    print()
    print("🏠 EM CASA")
    print("-" * 76)

    print(
        f"Jogos: "
        f"{profile['home_matches']}"
    )

    print(
        f"V/E/D: "
        f"{profile['home_wins']}/"
        f"{profile['home_draws']}/"
        f"{profile['home_losses']}"
    )

    print(
        f"Pontos: "
        f"{profile['home_points']}"
    )

    print(
        f"Aproveitamento: "
        f"{format_percentage(profile['home_performance_pct'])}"
    )

    # -------------------------------------------------------------------------
    # Fora
    # -------------------------------------------------------------------------

    print()
    print("✈️ FORA")
    print("-" * 76)

    print(
        f"Jogos: "
        f"{profile['away_matches']}"
    )

    print(
        f"V/E/D: "
        f"{profile['away_wins']}/"
        f"{profile['away_draws']}/"
        f"{profile['away_losses']}"
    )

    print(
        f"Pontos: "
        f"{profile['away_points']}"
    )

    print(
        f"Aproveitamento: "
        f"{format_percentage(profile['away_performance_pct'])}"
    )

    # -------------------------------------------------------------------------
    # Momento
    # -------------------------------------------------------------------------

    print()
    print("🔥 MOMENTO ATUAL")
    print("-" * 76)

    print(
        f"Últimos 5: "
        f"{profile['recent_form'] or '-'}"
    )

    print(
        f"Pontos nos últimos 5: "
        f"{profile['recent_points']}/15"
    )

    print(
        f"Aproveitamento recente: "
        f"{format_percentage(profile['recent_performance_pct'])}"
    )

    if recent_matches:

        print()
        print("Últimos jogos:")

        for game in recent_matches:

            icon = get_result_icon(
                game["result"]
            )

            home_away = (
                "CASA"
                if game["home"]
                else "FORA"
            )

            round_text = (
                f"R{game['round']}"
                if game["round"] is not None
                else "R?"
            )

            print(
                f"  {icon} "
                f"{round_text:<4} "
                f"{home_away:<4} | "
                f"{game['opponent']:<25} | "
                f"{game['goals_for']} x "
                f"{game['goals_against']}"
            )

    # -------------------------------------------------------------------------
    # Evolução
    # -------------------------------------------------------------------------

    print()
    print("📈 EVOLUÇÃO NO CAMPEONATO")
    print("-" * 76)

    print(
        f"Posição inicial reconstruída: "
        f"{format_position(evolution['initial_position'])}"
    )

    print(
        f"Melhor posição: "
        f"{format_position(evolution['best_position'])}"
    )

    print(
        f"Pior posição: "
        f"{format_position(evolution['worst_position'])}"
    )

    print(
        f"Posição atual: "
        f"{format_position(evolution['current_position'])}"
    )

    if (
        evolution[
            "position_change"
        ]
        is not None
    ):

        change = evolution[
            "position_change"
        ]

        if change > 0:

            print(
                f"Desde a primeira rodada: "
                f"subiu {change} posições 🚀"
            )

        elif change < 0:

            print(
                f"Desde a primeira rodada: "
                f"caiu {abs(change)} posições 📉"
            )

        else:

            print(
                "Desde a primeira rodada: "
                "mesma posição."
            )

    # -------------------------------------------------------------------------
    # Próximo jogo
    # -------------------------------------------------------------------------

    print()
    print("🗓️ PRÓXIMO JOGO")
    print("-" * 76)

    if next_match is None:

        print(
            "Nenhuma partida futura encontrada."
        )

    else:

        location = (
            "CASA"
            if next_match["home"]
            else "FORA"
        )

        print(
            f"Rodada: "
            f"{next_match['round'] or 'A definir'}"
        )

        print(
            f"Adversário: "
            f"{next_match['opponent']}"
        )

        print(
            f"Mando: "
            f"{location}"
        )

        print(
            f"Data: "
            f"{format_date(next_match['date'])}"
        )

        print(
            f"Horário: "
            f"{format_time(next_match['time'])}"
        )

        venue = (
            next_match[
                "venue"
            ]
            or "A definir"
        )

        print(
            f"Estádio: "
            f"{venue}"
        )

    # -------------------------------------------------------------------------
    # Pendências de rodadas passadas
    # -------------------------------------------------------------------------

    if not overdue_unscheduled_matches.empty:

        print()
        print("⏳ PENDÊNCIAS ATÉ A RODADA ATUAL")
        print("-" * 76)

        print(
            f"Quantidade: "
            f"{len(overdue_unscheduled_matches)}"
        )

        for _, match in (
            overdue_unscheduled_matches.iterrows()
        ):

            print_unscheduled_match(
                match,
                team_id,
                "⏳",
            )

    # -------------------------------------------------------------------------
    # Rodadas futuras ainda sem data
    # -------------------------------------------------------------------------

    if not upcoming_unscheduled_matches.empty:

        print()
        print("📅 JOGOS FUTUROS AINDA SEM DATA")
        print("-" * 76)

        print(
            f"Quantidade: "
            f"{len(upcoming_unscheduled_matches)}"
        )

        for _, match in (
            upcoming_unscheduled_matches.iterrows()
        ):

            print_unscheduled_match(
                match,
                team_id,
                "📅",
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
            "Exibe o relatório individual "
            "de um clube."
        )
    )

    parser.add_argument(
        "team",
        nargs="?",
        help=(
            "Nome ou ID do clube. "
            "Sem valor, utiliza o líder."
        ),
    )

    args = parser.parse_args()

    print_team_report(
        args.team
    )


if __name__ == "__main__":
    main()