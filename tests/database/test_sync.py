import pandas as pd

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
from brasileirao_data_lab.database.sync import (
    get_database_counts,
    optional_date,
    optional_int,
    optional_text,
    optional_time,
    sync_database,
    sync_matches,
    sync_standings_snapshots,
    sync_teams,
)


# =============================================================================
# Dataset
# =============================================================================


def create_sync_matches() -> pd.DataFrame:
    """
    Cria um pequeno campeonato com quatro clubes.

    Há três rodadas realizadas e
    uma rodada futura.
    """

    return pd.DataFrame(
        [
            # Rodada 1
            {
                "season": 2026,
                "round": 1,
                "match_id": 101,
                "match_number": 1,
                "group": "A",
                "date": "2026-01-10",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "home_goals": 2,
                "away_team_id": 2,
                "away_team": "Time B",
                "away_goals": 0,
                "venue": "Estádio A",
                "city": "Cidade A",
                "state": "SP",
                "championship": "Brasileirão",
            },
            {
                "season": 2026,
                "round": 1,
                "match_id": 102,
                "match_number": 2,
                "group": "A",
                "date": "2026-01-10",
                "time": "20:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "home_goals": 1,
                "away_team_id": 4,
                "away_team": "Time D",
                "away_goals": 0,
                "venue": "Estádio C",
                "city": "Cidade C",
                "state": "RJ",
                "championship": "Brasileirão",
            },

            # Rodada 2
            {
                "season": 2026,
                "round": 2,
                "match_id": 103,
                "match_number": 3,
                "group": "A",
                "date": "2026-01-17",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "home_goals": 1,
                "away_team_id": 3,
                "away_team": "Time C",
                "away_goals": 0,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
                "championship": "Brasileirão",
            },
            {
                "season": 2026,
                "round": 2,
                "match_id": 104,
                "match_number": 4,
                "group": "A",
                "date": "2026-01-17",
                "time": "20:00",
                "home_team_id": 4,
                "home_team": "Time D",
                "home_goals": 0,
                "away_team_id": 1,
                "away_team": "Time A",
                "away_goals": 0,
                "venue": "Estádio D",
                "city": "Cidade D",
                "state": "MG",
                "championship": "Brasileirão",
            },

            # Rodada 3
            {
                "season": 2026,
                "round": 3,
                "match_id": 105,
                "match_number": 5,
                "group": "A",
                "date": "2026-01-24",
                "time": "18:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "home_goals": 3,
                "away_team_id": 1,
                "away_team": "Time A",
                "away_goals": 1,
                "venue": "Estádio C",
                "city": "Cidade C",
                "state": "RJ",
                "championship": "Brasileirão",
            },
            {
                "season": 2026,
                "round": 3,
                "match_id": 106,
                "match_number": 6,
                "group": "A",
                "date": "2026-01-24",
                "time": "20:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "home_goals": 2,
                "away_team_id": 4,
                "away_team": "Time D",
                "away_goals": 0,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
                "championship": "Brasileirão",
            },

            # Rodada 4 futura
            {
                "season": 2026,
                "round": 4,
                "match_id": 107,
                "match_number": 7,
                "group": "A",
                "date": None,
                "time": None,
                "home_team_id": 1,
                "home_team": "Time A",
                "home_goals": None,
                "away_team_id": 3,
                "away_team": "Time C",
                "away_goals": None,
                "venue": None,
                "city": None,
                "state": None,
                "championship": "Brasileirão",
            },
            {
                "season": 2026,
                "round": 4,
                "match_id": 108,
                "match_number": 8,
                "group": "A",
                "date": None,
                "time": None,
                "home_team_id": 4,
                "home_team": "Time D",
                "home_goals": None,
                "away_team_id": 2,
                "away_team": "Time B",
                "away_goals": None,
                "venue": None,
                "city": None,
                "state": None,
                "championship": "Brasileirão",
            },
        ]
    )


def create_test_session():
    """Cria banco SQLite em memória."""

    engine = create_database_engine(
        "sqlite+pysqlite:///:memory:"
    )

    init_database(
        engine
    )

    session_factory = create_session_factory(
        engine
    )

    return session_factory()


# =============================================================================
# Conversores
# =============================================================================


def test_optional_converters():
    assert optional_int(
        3.0
    ) == 3

    assert optional_int(
        None
    ) is None

    assert optional_text(
        "  teste  "
    ) == "teste"

    assert optional_text(
        None
    ) is None

    assert (
        optional_date(
            "2026-08-18"
        ).isoformat()
        == "2026-08-18"
    )

    assert optional_date(
        None
    ) is None

    assert (
        optional_time(
            "19:30"
        ).strftime(
            "%H:%M"
        )
        == "19:30"
    )

    assert optional_time(
        None
    ) is None


# =============================================================================
# Times
# =============================================================================


def test_sync_teams_is_idempotent():
    matches = create_sync_matches()

    with create_test_session() as session:

        first = sync_teams(
            session,
            matches,
        )

        session.commit()

        assert first[
            "inserted"
        ] == 4

        second = sync_teams(
            session,
            matches,
        )

        session.commit()

        assert second[
            "inserted"
        ] == 0

        assert second[
            "updated"
        ] == 0

        assert second[
            "unchanged"
        ] == 4


# =============================================================================
# Partidas
# =============================================================================


def test_sync_matches_inserts_all_matches():
    matches = create_sync_matches()

    with create_test_session() as session:

        sync_teams(
            session,
            matches,
        )

        result = sync_matches(
            session,
            matches,
        )

        session.commit()

        assert result[
            "inserted"
        ] == 8

        counts = get_database_counts(
            session
        )

        assert counts[
            "matches"
        ] == 8


def test_sync_matches_updates_existing_match():
    matches = create_sync_matches()

    with create_test_session() as session:

        sync_teams(
            session,
            matches,
        )

        sync_matches(
            session,
            matches,
        )

        session.commit()

        updated_matches = matches.copy()

        updated_matches.loc[
            updated_matches[
                "match_id"
            ] == 107,
            [
                "date",
                "time",
                "home_goals",
                "away_goals",
                "venue",
            ],
        ] = [
            "2026-01-31",
            "18:30",
            2,
            1,
            "Novo Estádio",
        ]

        result = sync_matches(
            session,
            updated_matches,
        )

        session.commit()

        assert result[
            "inserted"
        ] == 0

        assert result[
            "updated"
        ] == 1

        saved = session.get(
            Match,
            107,
        )

        assert saved is not None

        assert saved.home_goals == 2
        assert saved.away_goals == 1

        assert (
            saved.date.isoformat()
            == "2026-01-31"
        )

        assert (
            saved.time.strftime(
                "%H:%M"
            )
            == "18:30"
        )

        assert (
            saved.venue
            == "Novo Estádio"
        )


# =============================================================================
# Snapshots
# =============================================================================


def test_sync_snapshots_inserts_history():
    matches = create_sync_matches()

    with create_test_session() as session:

        sync_teams(
            session,
            matches,
        )

        result = (
            sync_standings_snapshots(
                session,
                matches,
            )
        )

        session.commit()

        assert result[
            "inserted"
        ] == 12

        counts = get_database_counts(
            session
        )

        assert counts[
            "standings_snapshots"
        ] == 12


# =============================================================================
# Sincronização completa
# =============================================================================


def test_sync_database_populates_all_tables():
    matches = create_sync_matches()

    with create_test_session() as session:

        result = sync_database(
            session,
            matches,
        )

        session.commit()

        assert result[
            "counts"
        ] == {
            "teams": 4,
            "matches": 8,
            "standings_snapshots": 12,
        }


def test_sync_database_can_run_twice_without_duplicates():
    matches = create_sync_matches()

    with create_test_session() as session:

        first = sync_database(
            session,
            matches,
        )

        session.commit()

        second = sync_database(
            session,
            matches,
        )

        session.commit()

        assert first[
            "counts"
        ] == second[
            "counts"
        ]

        assert second[
            "counts"
        ] == {
            "teams": 4,
            "matches": 8,
            "standings_snapshots": 12,
        }

        assert second[
            "teams"
        ]["inserted"] == 0

        assert second[
            "matches"
        ]["inserted"] == 0

        assert second[
            "standings_snapshots"
        ]["inserted"] == 0


# =============================================================================
# Integridade dos dados
# =============================================================================


def test_database_contains_expected_entities():
    matches = create_sync_matches()

    with create_test_session() as session:

        sync_database(
            session,
            matches,
        )

        session.commit()

        team = session.get(
            Team,
            1,
        )

        match = session.get(
            Match,
            101,
        )

        snapshot = session.get(
            StandingsSnapshot,
            (
                2026,
                1,
                1,
            ),
        )

        assert team is not None
        assert team.name == "Time A"

        assert match is not None
        assert match.home_team_id == 1
        assert match.away_team_id == 2

        assert snapshot is not None
        assert snapshot.season == 2026
        assert snapshot.round == 1
        assert snapshot.team_id == 1