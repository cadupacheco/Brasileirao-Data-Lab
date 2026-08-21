from __future__ import annotations

from datetime import date

from sqlalchemy import (
    case,
    select,
)
from sqlalchemy.orm import Session

from brasileirao_data_lab.database.models import (
    Player,
    PlayerTeamCompetitionStat,
    Team,
)


# =============================================================================
# Clube
# =============================================================================


def get_team_or_none(
    session: Session,
    team_id: int,
) -> Team | None:
    """
    Retorna um clube pelo ID.
    """

    return session.get(
        Team,
        team_id,
    )


# =============================================================================
# Jogadores por clube
# =============================================================================


def get_team_players_from_database(
    session: Session,
    team_id: int,
    season: int,
    competition_id: int,
) -> list[dict]:
    """
    Retorna jogadores associados
    ao clube naquela temporada
    e competição.

    As estatísticas são específicas
    do clube informado.

    Isso é importante para casos
    de transferência durante
    a mesma competição.
    """

    statement = (
        select(
            Player.player_id.label(
                "player_id"
            ),
            Player.full_name.label(
                "full_name"
            ),
            Player.nickname.label(
                "nickname"
            ),
            Player.birth_date.label(
                "birth_date"
            ),
            Player.profile_url.label(
                "profile_url"
            ),
            Player.current_club_id.label(
                "current_club_id"
            ),
            Player.current_club_name.label(
                "current_club_name"
            ),
            Player.current_club_state.label(
                "current_club_state"
            ),
            Player.current_club_badge_url.label(
                "current_club_badge_url"
            ),
            PlayerTeamCompetitionStat.season.label(
                "season"
            ),
            PlayerTeamCompetitionStat.competition_id.label(
                "competition_id"
            ),
            PlayerTeamCompetitionStat.competition_name.label(
                "competition_name"
            ),
            PlayerTeamCompetitionStat.category.label(
                "category"
            ),
            PlayerTeamCompetitionStat.team_id.label(
                "team_id"
            ),
            Team.name.label(
                "team"
            ),
            PlayerTeamCompetitionStat.matches.label(
                "matches"
            ),
            PlayerTeamCompetitionStat.goals.label(
                "goals"
            ),
            PlayerTeamCompetitionStat.yellow_cards.label(
                "yellow_cards"
            ),
            PlayerTeamCompetitionStat.red_cards.label(
                "red_cards"
            ),
            case(
                (
                    Player.current_club_id
                    == PlayerTeamCompetitionStat.team_id,
                    True,
                ),
                else_=False,
            ).label(
                "is_current_club"
            ),
        )
        .join(
            Player,
            Player.player_id
            == PlayerTeamCompetitionStat.player_id,
        )
        .join(
            Team,
            Team.team_id
            == PlayerTeamCompetitionStat.team_id,
        )
        .where(
            PlayerTeamCompetitionStat.season
            == season,
            PlayerTeamCompetitionStat.competition_id
            == competition_id,
            PlayerTeamCompetitionStat.team_id
            == team_id,
        )
        .order_by(
            PlayerTeamCompetitionStat.matches.desc(),
            PlayerTeamCompetitionStat.goals.desc(),
            Player.nickname,
            Player.full_name,
        )
    )

    rows = (
        session.execute(
            statement
        )
        .mappings()
        .all()
    )

    return [
        dict(
            row
        )
        for row in rows
    ]


# =============================================================================
# Jogador específico
# =============================================================================


def get_team_player_from_database(
    session: Session,
    team_id: int,
    player_id: int,
    season: int,
    competition_id: int,
) -> dict | None:
    """
    Retorna um único jogador
    dentro do contexto do clube
    e competição.
    """

    players = (
        get_team_players_from_database(
            session=session,
            team_id=team_id,
            season=season,
            competition_id=competition_id,
        )
    )

    for player in players:
        if (
            int(
                player[
                    "player_id"
                ]
            )
            == player_id
        ):
            return player

    return None


# =============================================================================
# Idade
# =============================================================================


def calculate_age(
    birth_date: date | None,
    reference_date: date | None = None,
) -> int | None:
    """
    Calcula idade dinamicamente.

    Não armazenamos idade no banco
    porque ela muda com o tempo.
    """

    if birth_date is None:
        return None

    current_date = (
        reference_date
        or date.today()
    )

    age = (
        current_date.year
        - birth_date.year
    )

    birthday_has_not_happened = (
        (
            current_date.month,
            current_date.day,
        )
        <
        (
            birth_date.month,
            birth_date.day,
        )
    )

    if birthday_has_not_happened:
        age -= 1

    return age


def add_calculated_age(
    player: dict,
) -> dict:
    """
    Adiciona idade calculada
    ao objeto retornado pela consulta.
    """

    result = dict(
        player
    )

    result[
        "age"
    ] = calculate_age(
        player.get(
            "birth_date"
        )
    )

    return result


def get_team_players_with_age(
    session: Session,
    team_id: int,
    season: int,
    competition_id: int,
) -> list[dict]:
    """
    Consulta final usada pela API.
    """

    players = (
        get_team_players_from_database(
            session=session,
            team_id=team_id,
            season=season,
            competition_id=competition_id,
        )
    )

    return [
        add_calculated_age(
            player
        )
        for player in players
    ]