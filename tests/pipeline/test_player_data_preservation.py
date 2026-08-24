from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from brasileirao_data_lab.database.models import (
    Base,
    Player,
    PlayerTeamCompetitionStat,
    Team,
)
from brasileirao_data_lab.database.session import (
    create_database_engine,
)
from brasileirao_data_lab.pipelines.automated_project_update import (
    preserve_player_database_data,
)


def create_test_database(
    database_file: Path,
) -> None:
    """
    Cria um SQLite temporário usando
    os modelos reais do projeto.
    """

    database_url = (
        "sqlite:///"
        + database_file
        .resolve()
        .as_posix()
    )

    engine = create_database_engine(
        database_url
    )

    try:
        Base.metadata.create_all(
            engine
        )

    finally:
        engine.dispose()


def seed_source_database(
    database_file: Path,
) -> None:
    """
    Cria dados de exemplo representando
    um banco que já possui jogadores.
    """

    database_url = (
        "sqlite:///"
        + database_file
        .resolve()
        .as_posix()
    )

    engine = create_database_engine(
        database_url
    )

    try:
        with Session(
            engine
        ) as session:
            session.add_all(
                [
                    Team(
                        team_id=20001,
                        name="Corinthians",
                    ),
                    Team(
                        team_id=20002,
                        name="Palmeiras",
                    ),
                ]
            )

            session.add_all(
                [
                    Player(
                        player_id=1001,
                        full_name=(
                            "Jogador Um"
                        ),
                        nickname="Um",
                        birth_date=None,
                        profile_url=(
                            "https://example.com/1001"
                        ),
                        current_club_id=20001,
                        current_club_name=(
                            "Corinthians"
                        ),
                        current_club_state="SP",
                        current_club_badge_url=None,
                    ),
                    Player(
                        player_id=1002,
                        full_name=(
                            "Jogador Dois"
                        ),
                        nickname="Dois",
                        birth_date=None,
                        profile_url=(
                            "https://example.com/1002"
                        ),
                        current_club_id=20002,
                        current_club_name=(
                            "Palmeiras"
                        ),
                        current_club_state="SP",
                        current_club_badge_url=None,
                    ),
                ]
            )

            session.flush()

            session.add_all(
                [
                    PlayerTeamCompetitionStat(
                        season=2026,
                        competition_id=1260611,
                        player_id=1001,
                        team_id=20001,
                        competition_name=(
                            "Campeonato Brasileiro"
                        ),
                        category="Série A",
                        matches=10,
                        goals=3,
                        yellow_cards=2,
                        red_cards=0,
                    ),
                    PlayerTeamCompetitionStat(
                        season=2026,
                        competition_id=1260611,
                        player_id=1002,
                        team_id=20002,
                        competition_name=(
                            "Campeonato Brasileiro"
                        ),
                        category="Série A",
                        matches=12,
                        goals=5,
                        yellow_cards=1,
                        red_cards=0,
                    ),
                ]
            )

            session.commit()

    finally:
        engine.dispose()


def seed_target_teams(
    database_file: Path,
) -> None:
    """
    O banco reconstruído já possui
    os clubes criados pelo pipeline
    de partidas.

    Eles precisam existir antes da
    cópia das estatísticas por causa
    das Foreign Keys.
    """

    database_url = (
        "sqlite:///"
        + database_file
        .resolve()
        .as_posix()
    )

    engine = create_database_engine(
        database_url
    )

    try:
        with Session(
            engine
        ) as session:
            session.add_all(
                [
                    Team(
                        team_id=20001,
                        name="Corinthians",
                    ),
                    Team(
                        team_id=20002,
                        name="Palmeiras",
                    ),
                ]
            )

            session.commit()

    finally:
        engine.dispose()


def count_rows(
    database_file: Path,
    table_name: str,
) -> int:
    """
    Conta registros diretamente
    no SQLite.
    """

    with sqlite3.connect(
        database_file
    ) as connection:
        row = connection.execute(
            f'SELECT COUNT(*) '
            f'FROM "{table_name}"'
        ).fetchone()

    assert row is not None

    return int(
        row[0]
    )


def test_preserve_player_database_data(
    tmp_path: Path,
) -> None:
    """
    Jogadores e estatísticas precisam
    sobreviver à reconstrução do banco.
    """

    source_database = (
        tmp_path
        / "source.db"
    )

    target_database = (
        tmp_path
        / "target.db"
    )

    create_test_database(
        source_database
    )

    create_test_database(
        target_database
    )

    seed_source_database(
        source_database
    )

    seed_target_teams(
        target_database
    )

    result = (
        preserve_player_database_data(
            source_database_file=(
                source_database
            ),
            target_database_file=(
                target_database
            ),
        )
    )

    assert result.players == 2
    assert result.player_stats == 2

    assert (
        count_rows(
            source_database,
            "players",
        )
        == 2
    )

    assert (
        count_rows(
            target_database,
            "players",
        )
        == 2
    )

    assert (
        count_rows(
            source_database,
            "player_team_competition_stats",
        )
        == 2
    )

    assert (
        count_rows(
            target_database,
            "player_team_competition_stats",
        )
        == 2
    )


def test_preserved_player_values_are_identical(
    tmp_path: Path,
) -> None:
    """
    Não basta preservar a quantidade.
    Os valores também precisam ser
    exatamente iguais.
    """

    source_database = (
        tmp_path
        / "source.db"
    )

    target_database = (
        tmp_path
        / "target.db"
    )

    create_test_database(
        source_database
    )

    create_test_database(
        target_database
    )

    seed_source_database(
        source_database
    )

    seed_target_teams(
        target_database
    )

    preserve_player_database_data(
        source_database_file=(
            source_database
        ),
        target_database_file=(
            target_database
        ),
    )

    with sqlite3.connect(
        source_database
    ) as source_connection, sqlite3.connect(
        target_database
    ) as target_connection:

        source_players = (
            source_connection.execute(
                """
                SELECT
                    player_id,
                    full_name,
                    nickname,
                    current_club_id,
                    current_club_name
                FROM players
                ORDER BY player_id
                """
            ).fetchall()
        )

        target_players = (
            target_connection.execute(
                """
                SELECT
                    player_id,
                    full_name,
                    nickname,
                    current_club_id,
                    current_club_name
                FROM players
                ORDER BY player_id
                """
            ).fetchall()
        )

        source_stats = (
            source_connection.execute(
                """
                SELECT
                    season,
                    competition_id,
                    player_id,
                    team_id,
                    matches,
                    goals,
                    yellow_cards,
                    red_cards
                FROM player_team_competition_stats
                ORDER BY
                    season,
                    competition_id,
                    player_id,
                    team_id
                """
            ).fetchall()
        )

        target_stats = (
            target_connection.execute(
                """
                SELECT
                    season,
                    competition_id,
                    player_id,
                    team_id,
                    matches,
                    goals,
                    yellow_cards,
                    red_cards
                FROM player_team_competition_stats
                ORDER BY
                    season,
                    competition_id,
                    player_id,
                    team_id
                """
            ).fetchall()
        )

    assert target_players == source_players
    assert target_stats == source_stats


def test_source_without_player_tables_is_allowed(
    tmp_path: Path,
) -> None:
    """
    Compatibilidade com bancos antigos
    anteriores à feature de jogadores.
    """

    source_database = (
        tmp_path
        / "legacy.db"
    )

    target_database = (
        tmp_path
        / "target.db"
    )

    with sqlite3.connect(
        source_database
    ) as connection:
        connection.execute(
            """
            CREATE TABLE legacy_data (
                id INTEGER PRIMARY KEY
            )
            """
        )

        connection.commit()

    create_test_database(
        target_database
    )

    result = (
        preserve_player_database_data(
            source_database_file=(
                source_database
            ),
            target_database_file=(
                target_database
            ),
        )
    )

    assert result.players == 0
    assert result.player_stats == 0

    assert (
        count_rows(
            target_database,
            "players",
        )
        == 0
    )

    assert (
        count_rows(
            target_database,
            "player_team_competition_stats",
        )
        == 0
    )


def test_target_with_existing_player_data_is_rejected(
    tmp_path: Path,
) -> None:
    """
    O banco temporário deve estar limpo
    antes da preservação.

    Isso evita duplicações silenciosas.
    """

    source_database = (
        tmp_path
        / "source.db"
    )

    target_database = (
        tmp_path
        / "target.db"
    )

    create_test_database(
        source_database
    )

    create_test_database(
        target_database
    )

    seed_source_database(
        source_database
    )

    seed_source_database(
        target_database
    )

    with pytest.raises(
        ValueError,
        match=(
            "Banco temporário deveria "
            "estar sem dados de jogadores"
        ),
    ):
        preserve_player_database_data(
            source_database_file=(
                source_database
            ),
            target_database_file=(
                target_database
            ),
        )