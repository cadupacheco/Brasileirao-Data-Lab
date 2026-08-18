from datetime import (
    date,
    time,
)

import pytest
from sqlalchemy import (
    select,
)
from sqlalchemy.exc import (
    IntegrityError,
)

from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.database.models import (
    Match,
    StandingsSnapshot,
    Team,
)
from brasileirao_data_lab.database.session import (
    create_database_engine,
    create_session_factory,
)


# =============================================================================
# Helpers
# =============================================================================


def create_test_database():
    """
    Cria um banco SQLite temporário
    inteiramente em memória.
    """

    engine = create_database_engine(
        "sqlite+pysqlite:///:memory:"
    )

    init_database(
        engine
    )

    session_factory = (
        create_session_factory(
            engine
        )
    )

    return (
        engine,
        session_factory,
    )


# =============================================================================
# Estrutura
# =============================================================================


def test_database_tables_are_created():
    engine, _ = (
        create_test_database()
    )

    tables = init_database(
        engine
    )

    assert tables == [
        "matches",
        "standings_snapshots",
        "teams",
    ]


# =============================================================================
# Times
# =============================================================================


def test_team_can_be_inserted():
    _, session_factory = (
        create_test_database()
    )

    with session_factory() as session:

        team = Team(
            team_id=20001,
            name="Corinthians",
        )

        session.add(
            team
        )

        session.commit()

        saved_team = session.get(
            Team,
            20001,
        )

        assert saved_team is not None

        assert (
            saved_team.name
            == "Corinthians"
        )


# =============================================================================
# Partidas
# =============================================================================


def test_match_can_be_inserted():
    _, session_factory = (
        create_test_database()
    )

    with session_factory() as session:

        home = Team(
            team_id=1,
            name="Time A",
        )

        away = Team(
            team_id=2,
            name="Time B",
        )

        session.add_all(
            [
                home,
                away,
            ]
        )

        session.commit()

        match = Match(
            match_id=1001,
            season=2026,
            round=1,
            match_number=1,
            group="A",
            date=date(
                2026,
                1,
                10,
            ),
            time=time(
                18,
                30,
            ),
            home_team_id=1,
            home_goals=2,
            away_team_id=2,
            away_goals=1,
            venue="Estádio A",
            city="São Paulo",
            state="SP",
            championship=(
                "Campeonato Brasileiro"
            ),
        )

        session.add(
            match
        )

        session.commit()

        saved_match = session.get(
            Match,
            1001,
        )

        assert saved_match is not None

        assert (
            saved_match.season
            == 2026
        )

        assert (
            saved_match.round
            == 1
        )

        assert (
            saved_match.home_goals
            == 2
        )

        assert (
            saved_match.away_goals
            == 1
        )


# =============================================================================
# Snapshots
# =============================================================================


def test_standings_snapshot_can_be_inserted():
    _, session_factory = (
        create_test_database()
    )

    with session_factory() as session:

        team = Team(
            team_id=1,
            name="Time A",
        )

        session.add(
            team
        )

        session.commit()

        snapshot = StandingsSnapshot(
            season=2026,
            round=10,
            team_id=1,
            position=2,
            matches=10,
            wins=6,
            draws=2,
            losses=2,
            goals_for=20,
            goals_against=10,
            goal_difference=10,
            points=20,
            performance_pct=66.67,
        )

        session.add(
            snapshot
        )

        session.commit()

        statement = select(
            StandingsSnapshot
        ).where(
            StandingsSnapshot.season
            == 2026,
            StandingsSnapshot.round
            == 10,
            StandingsSnapshot.team_id
            == 1,
        )

        saved_snapshot = (
            session.execute(
                statement
            )
            .scalar_one()
        )

        assert (
            saved_snapshot.position
            == 2
        )

        assert (
            saved_snapshot.points
            == 20
        )


# =============================================================================
# Integridade referencial
# =============================================================================


def test_match_requires_existing_teams():
    _, session_factory = (
        create_test_database()
    )

    with session_factory() as session:

        match = Match(
            match_id=9999,
            season=2026,
            round=1,
            match_number=1,
            home_team_id=999,
            home_goals=None,
            away_team_id=998,
            away_goals=None,
        )

        session.add(
            match
        )

        with pytest.raises(
            IntegrityError
        ):

            session.commit()

        session.rollback()