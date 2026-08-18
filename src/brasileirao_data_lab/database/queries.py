from __future__ import annotations

import argparse
from datetime import date, time
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from brasileirao_data_lab.database.models import (
    Match,
)
from brasileirao_data_lab.database.repository import (
    get_matches_by_round,
    get_recent_team_matches_from_database,
    get_standings_by_round,
    get_team_matches_from_database,
    get_team_standings_history,
    get_upcoming_team_matches_from_database,
    resolve_team_from_database,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
)


# =============================================================================
# Temporada
# =============================================================================


def get_latest_database_season(
    session: Session,
) -> int:
    """
    Retorna a temporada mais recente
    armazenada no banco.
    """

    statement = select(
        func.max(
            Match.season
        )
    )

    season = session.scalar(
        statement
    )

    if season is None:

        raise ValueError(
            "O banco ainda não possui partidas."
        )

    return int(
        season
    )


def resolve_database_season(
    session: Session,
    season: int | None = None,
) -> int:
    """
    Resolve a temporada da consulta.

    Se nenhuma temporada for informada,
    utiliza a mais recente disponível no banco.
    """

    if season is not None:

        if season <= 0:

            raise ValueError(
                "A temporada deve ser maior que zero."
            )

        return int(
            season
        )

    return get_latest_database_season(
        session
    )


# =============================================================================
# Formatação
# =============================================================================


def format_database_date(
    value: date | None,
) -> str:
    """Formata uma data para exibição."""

    if value is None:
        return "A definir"

    return value.strftime(
        "%d/%m/%Y"
    )


def format_database_time(
    value: time | None,
) -> str:
    """Formata um horário para exibição."""

    if value is None:
        return "A definir"

    return value.strftime(
        "%H:%M"
    )


def format_match_score(
    match: dict[str, Any],
) -> str:
    """
    Formata o placar de uma partida.

    Jogos futuros recebem '- x -'.
    """

    home_goals = match[
        "home_goals"
    ]

    away_goals = match[
        "away_goals"
    ]

    if (
        home_goals is None
        or away_goals is None
    ):

        return "- x -"

    return (
        f"{home_goals} x "
        f"{away_goals}"
    )


def format_team_perspective(
    match: dict[str, Any],
    team_id: int,
) -> tuple[
    str,
    str,
]:
    """
    Retorna mando e adversário
    pela perspectiva de um clube.
    """

    if (
        match[
            "home_team_id"
        ]
        == team_id
    ):

        return (
            "CASA",
            match[
                "away_team"
            ],
        )

    return (
        "FORA",
        match[
            "home_team"
        ],
    )


# =============================================================================
# Clube
# =============================================================================


def print_team_query(
    session: Session,
    identifier: int | str,
    season: int | None = None,
) -> None:
    """
    Exibe um resumo de um clube
    utilizando somente o SQLite.
    """

    selected_season = (
        resolve_database_season(
            session,
            season,
        )
    )

    team = (
        resolve_team_from_database(
            session,
            identifier,
        )
    )

    matches = (
        get_team_matches_from_database(
            session,
            team_id=team.team_id,
            season=selected_season,
        )
    )

    history = (
        get_team_standings_history(
            session,
            season=selected_season,
            team_id=team.team_id,
        )
    )

    played_matches = [
        match
        for match in matches
        if (
            match[
                "home_goals"
            ]
            is not None
            and match[
                "away_goals"
            ]
            is not None
        )
    ]

    future_matches = [
        match
        for match in matches
        if (
            match[
                "home_goals"
            ]
            is None
            or match[
                "away_goals"
            ]
            is None
        )
    ]

    print()
    print("⚽ Brasileirão Data Lab")
    print("🗄️ Database Query - Clube")
    print("=" * 72)

    print()
    print(
        f"Clube: {team.name}"
    )

    print(
        f"ID CBF: {team.team_id}"
    )

    print(
        f"Temporada: {selected_season}"
    )

    print()
    print(
        f"Partidas cadastradas: "
        f"{len(matches)}"
    )

    print(
        f"Partidas realizadas: "
        f"{len(played_matches)}"
    )

    print(
        f"Partidas futuras: "
        f"{len(future_matches)}"
    )

    if history:

        current = history[
            -1
        ]

        print()
        print("CLASSIFICAÇÃO")
        print("-" * 72)

        print(
            f"Posição: "
            f"{current['position']}º"
        )

        print(
            f"Pontos: "
            f"{current['points']}"
        )

        print(
            f"Jogos: "
            f"{current['matches']}"
        )

        print(
            f"V/E/D: "
            f"{current['wins']}/"
            f"{current['draws']}/"
            f"{current['losses']}"
        )

        print(
            f"Saldo: "
            f"{current['goal_difference']:+d}"
        )

    print()
    print("=" * 72)


# =============================================================================
# Rodada
# =============================================================================


def print_round_query(
    session: Session,
    round_number: int,
    season: int | None = None,
) -> None:
    """Exibe os jogos de uma rodada."""

    if not (
        1
        <= round_number
        <= 38
    ):

        raise ValueError(
            "A rodada deve estar entre 1 e 38."
        )

    selected_season = (
        resolve_database_season(
            session,
            season,
        )
    )

    matches = get_matches_by_round(
        session,
        season=selected_season,
        round_number=round_number,
    )

    print()
    print("⚽ Brasileirão Data Lab")
    print("🗄️ Database Query - Rodada")
    print("=" * 72)

    print()
    print(
        f"Temporada: {selected_season}"
    )

    print(
        f"Rodada: {round_number}"
    )

    print(
        f"Partidas: {len(matches)}"
    )

    print()
    print("-" * 72)

    for match in matches:

        date_text = (
            format_database_date(
                match["date"]
            )
        )

        time_text = (
            format_database_time(
                match["time"]
            )
        )

        score = format_match_score(
            match
        )

        print(
            f"{date_text} "
            f"{time_text:<7} | "
            f"{match['home_team']:<25} "
            f"{score:^7} "
            f"{match['away_team']}"
        )

    print()
    print("=" * 72)


# =============================================================================
# Jogos recentes
# =============================================================================


def print_recent_query(
    session: Session,
    identifier: int | str,
    season: int | None = None,
    limit: int = 5,
) -> None:
    """Exibe os últimos jogos realizados."""

    selected_season = (
        resolve_database_season(
            session,
            season,
        )
    )

    team = resolve_team_from_database(
        session,
        identifier,
    )

    matches = (
        get_recent_team_matches_from_database(
            session,
            team_id=team.team_id,
            season=selected_season,
            limit=limit,
        )
    )

    print()
    print("⚽ Brasileirão Data Lab")
    print("🗄️ Database Query - Jogos recentes")
    print("=" * 72)

    print()
    print(
        f"{team.name} | "
        f"Temporada {selected_season}"
    )

    print()
    print("-" * 72)

    for match in matches:

        location, opponent = (
            format_team_perspective(
                match,
                team.team_id,
            )
        )

        if location == "CASA":

            goals_for = match[
                "home_goals"
            ]

            goals_against = match[
                "away_goals"
            ]

        else:

            goals_for = match[
                "away_goals"
            ]

            goals_against = match[
                "home_goals"
            ]

        if goals_for > goals_against:

            result = "V"

        elif goals_for == goals_against:

            result = "E"

        else:

            result = "D"

        print(
            f"R{match['round']:<2} "
            f"{location:<4} | "
            f"{opponent:<25} | "
            f"{goals_for} x "
            f"{goals_against} | "
            f"{result}"
        )

    print()
    print("=" * 72)


# =============================================================================
# Próximos jogos
# =============================================================================


def print_upcoming_query(
    session: Session,
    identifier: int | str,
    season: int | None = None,
    limit: int = 5,
) -> None:
    """Exibe os próximos jogos do clube."""

    selected_season = (
        resolve_database_season(
            session,
            season,
        )
    )

    team = resolve_team_from_database(
        session,
        identifier,
    )

    matches = (
        get_upcoming_team_matches_from_database(
            session,
            team_id=team.team_id,
            season=selected_season,
            limit=limit,
        )
    )

    print()
    print("⚽ Brasileirão Data Lab")
    print("🗄️ Database Query - Próximos jogos")
    print("=" * 72)

    print()
    print(
        f"{team.name} | "
        f"Temporada {selected_season}"
    )

    print()
    print("-" * 72)

    for match in matches:

        location, opponent = (
            format_team_perspective(
                match,
                team.team_id,
            )
        )

        print(
            f"R{match['round']:<2} "
            f"{location:<4} | "
            f"{opponent:<25} | "
            f"{format_database_date(match['date'])} | "
            f"{format_database_time(match['time'])}"
        )

    print()
    print("=" * 72)


# =============================================================================
# Classificação
# =============================================================================


def print_standings_query(
    session: Session,
    round_number: int,
    season: int | None = None,
) -> None:
    """Exibe a classificação de uma rodada."""

    if not (
        1
        <= round_number
        <= 38
    ):

        raise ValueError(
            "A rodada deve estar entre 1 e 38."
        )

    selected_season = (
        resolve_database_season(
            session,
            season,
        )
    )

    standings = (
        get_standings_by_round(
            session,
            season=selected_season,
            round_number=round_number,
        )
    )

    print()
    print("⚽ Brasileirão Data Lab")
    print("🗄️ Database Query - Classificação")
    print("=" * 78)

    print()
    print(
        f"Temporada {selected_season} | "
        f"Rodada {round_number}"
    )

    print()
    print(
        f"{'#':>2} "
        f"{'Clube':<26} "
        f"{'J':>3} "
        f"{'V':>3} "
        f"{'E':>3} "
        f"{'D':>3} "
        f"{'GP':>3} "
        f"{'GC':>3} "
        f"{'SG':>4} "
        f"{'PTS':>4}"
    )

    print("-" * 78)

    for item in standings:

        print(
            f"{item['position']:>2} "
            f"{item['team']:<26} "
            f"{item['matches']:>3} "
            f"{item['wins']:>3} "
            f"{item['draws']:>3} "
            f"{item['losses']:>3} "
            f"{item['goals_for']:>3} "
            f"{item['goals_against']:>3} "
            f"{item['goal_difference']:>+4} "
            f"{item['points']:>4}"
        )

    print()
    print("=" * 78)


# =============================================================================
# Histórico
# =============================================================================


def print_history_query(
    session: Session,
    identifier: int | str,
    season: int | None = None,
) -> None:
    """Exibe a evolução de classificação de um clube."""

    selected_season = (
        resolve_database_season(
            session,
            season,
        )
    )

    team = resolve_team_from_database(
        session,
        identifier,
    )

    history = (
        get_team_standings_history(
            session,
            season=selected_season,
            team_id=team.team_id,
        )
    )

    print()
    print("⚽ Brasileirão Data Lab")
    print("🗄️ Database Query - Histórico")
    print("=" * 72)

    print()
    print(
        f"{team.name} | "
        f"Temporada {selected_season}"
    )

    print()
    print(
        f"{'Rodada':>6} "
        f"{'Posição':>8} "
        f"{'Jogos':>6} "
        f"{'Pontos':>7}"
    )

    print("-" * 72)

    for item in history:

        print(
            f"{item['round']:>6} "
            f"{item['position']:>7}º "
            f"{item['matches']:>6} "
            f"{item['points']:>7}"
        )

    print()
    print("=" * 72)


# =============================================================================
# CLI
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Cria o parser da CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "Consulta o banco SQLite do "
            "Brasileirão Data Lab."
        )
    )

    parser.add_argument(
        "--season",
        type=int,
        default=None,
        help=(
            "Temporada. "
            "Por padrão usa a mais recente do banco."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # -------------------------------------------------------------------------
    # team
    # -------------------------------------------------------------------------

    team_parser = subparsers.add_parser(
        "team",
        help="Resumo de um clube.",
    )

    team_parser.add_argument(
        "team",
        help="Nome ou ID do clube.",
    )

    # -------------------------------------------------------------------------
    # round
    # -------------------------------------------------------------------------

    round_parser = subparsers.add_parser(
        "round",
        help="Jogos de uma rodada.",
    )

    round_parser.add_argument(
        "round",
        type=int,
        help="Número da rodada.",
    )

    # -------------------------------------------------------------------------
    # recent
    # -------------------------------------------------------------------------

    recent_parser = subparsers.add_parser(
        "recent",
        help="Últimos jogos de um clube.",
    )

    recent_parser.add_argument(
        "team",
        help="Nome ou ID do clube.",
    )

    recent_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Quantidade de jogos.",
    )

    # -------------------------------------------------------------------------
    # upcoming
    # -------------------------------------------------------------------------

    upcoming_parser = (
        subparsers.add_parser(
            "upcoming",
            help="Próximos jogos de um clube.",
        )
    )

    upcoming_parser.add_argument(
        "team",
        help="Nome ou ID do clube.",
    )

    upcoming_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Quantidade de jogos.",
    )

    # -------------------------------------------------------------------------
    # standings
    # -------------------------------------------------------------------------

    standings_parser = (
        subparsers.add_parser(
            "standings",
            help="Classificação por rodada.",
        )
    )

    standings_parser.add_argument(
        "round",
        type=int,
        help="Número da rodada.",
    )

    # -------------------------------------------------------------------------
    # history
    # -------------------------------------------------------------------------

    history_parser = (
        subparsers.add_parser(
            "history",
            help=(
                "Histórico de classificação "
                "de um clube."
            ),
        )
    )

    history_parser.add_argument(
        "team",
        help="Nome ou ID do clube.",
    )

    return parser


def main() -> None:
    """Entrada principal da CLI."""

    parser = create_parser()

    args = parser.parse_args()

    with SessionLocal() as session:

        if args.command == "team":

            print_team_query(
                session,
                args.team,
                season=args.season,
            )

        elif args.command == "round":

            print_round_query(
                session,
                args.round,
                season=args.season,
            )

        elif args.command == "recent":

            print_recent_query(
                session,
                args.team,
                season=args.season,
                limit=args.limit,
            )

        elif args.command == "upcoming":

            print_upcoming_query(
                session,
                args.team,
                season=args.season,
                limit=args.limit,
            )

        elif args.command == "standings":

            print_standings_query(
                session,
                args.round,
                season=args.season,
            )

        elif args.command == "history":

            print_history_query(
                session,
                args.team,
                season=args.season,
            )


if __name__ == "__main__":
    main()