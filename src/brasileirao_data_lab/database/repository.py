from __future__ import annotations

from typing import Any

from sqlalchemy import (
    case,
    func,
    or_,
    select,
)
from sqlalchemy.orm import (
    Session,
    aliased,
)

from brasileirao_data_lab.database.models import (
    Match,
    StandingsSnapshot,
    Team,
)


# =============================================================================
# Clubes
# =============================================================================


def resolve_team_from_database(
    session: Session,
    identifier: int | str,
) -> Team:
    """
    Resolve um clube por:

    - ID inteiro
    - ID em texto
    - nome exato
    - trecho único do nome

    Exemplos:

        20001
        "20001"
        "Corinthians"
        "Palmeiras"
    """

    # -------------------------------------------------------------------------
    # ID inteiro
    # -------------------------------------------------------------------------

    if isinstance(
        identifier,
        int,
    ):

        team = session.get(
            Team,
            identifier,
        )

        if team is None:

            raise ValueError(
                f"Clube não encontrado: "
                f"{identifier}"
            )

        return team

    identifier_text = str(
        identifier
    ).strip()

    if not identifier_text:

        raise ValueError(
            "Identificador do clube "
            "não pode ser vazio."
        )

    # -------------------------------------------------------------------------
    # ID numérico em texto
    # -------------------------------------------------------------------------

    if identifier_text.isdigit():

        team = session.get(
            Team,
            int(
                identifier_text
            ),
        )

        if team is None:

            raise ValueError(
                f"Clube não encontrado: "
                f"{identifier}"
            )

        return team

    normalized_name = (
        identifier_text.casefold()
    )

    # -------------------------------------------------------------------------
    # Nome exato
    # -------------------------------------------------------------------------

    exact_statement = (
        select(
            Team
        )
        .where(
            func.lower(
                Team.name
            )
            == normalized_name.lower()
        )
    )

    exact_team = session.scalar(
        exact_statement
    )

    if exact_team is not None:

        return exact_team

    # -------------------------------------------------------------------------
    # Busca parcial
    # -------------------------------------------------------------------------

    partial_statement = (
        select(
            Team
        )
        .where(
            func.lower(
                Team.name
            ).like(
                f"%{normalized_name.lower()}%"
            )
        )
        .order_by(
            Team.name
        )
    )

    candidates = list(
        session.scalars(
            partial_statement
        )
    )

    if not candidates:

        raise ValueError(
            f"Clube não encontrado: "
            f"{identifier}"
        )

    if len(
        candidates
    ) > 1:

        names = ", ".join(
            team.name
            for team in candidates
        )

        raise ValueError(
            "Identificador ambíguo. "
            f"Encontrados: {names}"
        )

    return candidates[0]


# =============================================================================
# Consulta base de partidas
# =============================================================================


def execute_match_query(
    session: Session,
    statement,
) -> list[dict[str, Any]]:
    """
    Executa uma consulta de partidas
    incluindo os nomes dos clubes.
    """

    rows = session.execute(
        statement
    ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def create_match_select():
    """
    Cria o SELECT base utilizado
    pelas consultas de partidas.
    """

    home_team = aliased(
        Team
    )

    away_team = aliased(
        Team
    )

    statement = (
        select(
            Match.match_id.label(
                "match_id"
            ),
            Match.season.label(
                "season"
            ),
            Match.round.label(
                "round"
            ),
            Match.match_number.label(
                "match_number"
            ),
            Match.group.label(
                "group"
            ),
            Match.date.label(
                "date"
            ),
            Match.time.label(
                "time"
            ),
            Match.home_team_id.label(
                "home_team_id"
            ),
            home_team.name.label(
                "home_team"
            ),
            Match.home_goals.label(
                "home_goals"
            ),
            Match.away_team_id.label(
                "away_team_id"
            ),
            away_team.name.label(
                "away_team"
            ),
            Match.away_goals.label(
                "away_goals"
            ),
            Match.venue.label(
                "venue"
            ),
            Match.city.label(
                "city"
            ),
            Match.state.label(
                "state"
            ),
            Match.championship.label(
                "championship"
            ),
        )
        .join(
            home_team,
            Match.home_team_id
            == home_team.team_id,
        )
        .join(
            away_team,
            Match.away_team_id
            == away_team.team_id,
        )
    )

    return statement


# =============================================================================
# Partidas por rodada
# =============================================================================


def get_matches_by_round(
    session: Session,
    season: int,
    round_number: int,
) -> list[dict[str, Any]]:
    """
    Retorna todas as partidas
    de uma rodada.
    """

    statement = (
        create_match_select()
        .where(
            Match.season
            == season,
            Match.round
            == round_number,
        )
        .order_by(
            Match.match_number,
            Match.match_id,
        )
    )

    return execute_match_query(
        session,
        statement,
    )


# =============================================================================
# Partidas de um clube
# =============================================================================


def get_team_matches_from_database(
    session: Session,
    team_id: int,
    season: int,
) -> list[dict[str, Any]]:
    """
    Retorna todas as partidas de um clube
    na temporada.
    """

    statement = (
        create_match_select()
        .where(
            Match.season
            == season,
            or_(
                Match.home_team_id
                == team_id,
                Match.away_team_id
                == team_id,
            ),
        )
        .order_by(
            Match.round,
            Match.match_number,
            Match.match_id,
        )
    )

    return execute_match_query(
        session,
        statement,
    )


# =============================================================================
# Jogos recentes
# =============================================================================


def get_recent_team_matches_from_database(
    session: Session,
    team_id: int,
    season: int,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Retorna os últimos jogos realizados
    de um clube.

    Jogos sem placar são ignorados.
    """

    if limit <= 0:

        raise ValueError(
            "limit deve ser maior que zero."
        )

    statement = (
        create_match_select()
        .where(
            Match.season
            == season,
            or_(
                Match.home_team_id
                == team_id,
                Match.away_team_id
                == team_id,
            ),
            Match.home_goals.is_not(
                None
            ),
            Match.away_goals.is_not(
                None
            ),
        )
        .order_by(
            case(
                (
                    Match.date.is_(
                        None
                    ),
                    1,
                ),
                else_=0,
            ),
            Match.date.desc(),
            Match.time.desc(),
            Match.round.desc(),
            Match.match_number.desc(),
        )
        .limit(
            limit
        )
    )

    return execute_match_query(
        session,
        statement,
    )


# =============================================================================
# Próximos jogos
# =============================================================================


def get_upcoming_team_matches_from_database(
    session: Session,
    team_id: int,
    season: int,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Retorna partidas ainda sem placar.

    Jogos com data definida aparecem primeiro.
    Jogos adiados ou ainda sem calendário
    ficam posteriormente ordenados pela rodada.
    """

    if (
        limit is not None
        and limit <= 0
    ):

        raise ValueError(
            "limit deve ser maior que zero."
        )

    statement = (
        create_match_select()
        .where(
            Match.season
            == season,
            or_(
                Match.home_team_id
                == team_id,
                Match.away_team_id
                == team_id,
            ),
            Match.home_goals.is_(
                None
            ),
            Match.away_goals.is_(
                None
            ),
        )
        .order_by(
            case(
                (
                    Match.date.is_(
                        None
                    ),
                    1,
                ),
                else_=0,
            ),
            Match.date.asc(),
            Match.time.asc(),
            Match.round.asc(),
            Match.match_number.asc(),
        )
    )

    if limit is not None:

        statement = statement.limit(
            limit
        )

    return execute_match_query(
        session,
        statement,
    )


# =============================================================================
# Classificação por rodada
# =============================================================================


def get_standings_by_round(
    session: Session,
    season: int,
    round_number: int,
) -> list[dict[str, Any]]:
    """
    Retorna a classificação armazenada
    para uma rodada específica.
    """

    statement = (
        select(
            StandingsSnapshot.season.label(
                "season"
            ),
            StandingsSnapshot.round.label(
                "round"
            ),
            StandingsSnapshot.team_id.label(
                "team_id"
            ),
            Team.name.label(
                "team"
            ),
            StandingsSnapshot.position.label(
                "position"
            ),
            StandingsSnapshot.matches.label(
                "matches"
            ),
            StandingsSnapshot.wins.label(
                "wins"
            ),
            StandingsSnapshot.draws.label(
                "draws"
            ),
            StandingsSnapshot.losses.label(
                "losses"
            ),
            StandingsSnapshot.goals_for.label(
                "goals_for"
            ),
            StandingsSnapshot.goals_against.label(
                "goals_against"
            ),
            StandingsSnapshot.goal_difference.label(
                "goal_difference"
            ),
            StandingsSnapshot.points.label(
                "points"
            ),
            StandingsSnapshot.performance_pct.label(
                "performance_pct"
            ),
        )
        .join(
            Team,
            StandingsSnapshot.team_id
            == Team.team_id,
        )
        .where(
            StandingsSnapshot.season
            == season,
            StandingsSnapshot.round
            == round_number,
        )
        .order_by(
            StandingsSnapshot.position
        )
    )

    rows = session.execute(
        statement
    ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


# =============================================================================
# Histórico de classificação
# =============================================================================


def get_team_standings_history(
    session: Session,
    season: int,
    team_id: int,
) -> list[dict[str, Any]]:
    """
    Retorna a evolução de um clube
    rodada por rodada.
    """

    statement = (
        select(
            StandingsSnapshot.season.label(
                "season"
            ),
            StandingsSnapshot.round.label(
                "round"
            ),
            StandingsSnapshot.team_id.label(
                "team_id"
            ),
            Team.name.label(
                "team"
            ),
            StandingsSnapshot.position.label(
                "position"
            ),
            StandingsSnapshot.matches.label(
                "matches"
            ),
            StandingsSnapshot.points.label(
                "points"
            ),
            StandingsSnapshot.wins.label(
                "wins"
            ),
            StandingsSnapshot.draws.label(
                "draws"
            ),
            StandingsSnapshot.losses.label(
                "losses"
            ),
            StandingsSnapshot.goals_for.label(
                "goals_for"
            ),
            StandingsSnapshot.goals_against.label(
                "goals_against"
            ),
            StandingsSnapshot.goal_difference.label(
                "goal_difference"
            ),
            StandingsSnapshot.performance_pct.label(
                "performance_pct"
            ),
        )
        .join(
            Team,
            StandingsSnapshot.team_id
            == Team.team_id,
        )
        .where(
            StandingsSnapshot.season
            == season,
            StandingsSnapshot.team_id
            == team_id,
        )
        .order_by(
            StandingsSnapshot.round
        )
    )

    rows = session.execute(
        statement
    ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]