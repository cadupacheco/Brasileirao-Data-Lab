import pandas as pd

from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.database.models import (
    Match,
    Team,
)
from brasileirao_data_lab.database.session import (
    create_database_engine,
    create_session_factory,
)
from brasileirao_data_lab.database.sync import (
    sync_database,
)
from brasileirao_data_lab.database.validate import (
    compare_matches_dataframes,
    load_matches_from_database,
    normalize_matches_dataframe,
    validate_database_against_matches,
)


# =============================================================================
# Dataset
# =============================================================================


def create_validation_matches() -> pd.DataFrame:
    """Dataset pequeno para validar CSV x Database."""

    return pd.DataFrame(
        [
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
            {
                "season": 2026,
                "round": 2,
                "match_id": 103,
                "match_number": 3,
                "group": "A",
                "date": "2026-01-17",
                "time": "18:30",
                "home_team_id": 2,
                "home_team": "Time B",
                "home_goals": 1,
                "away_team_id": 3,
                "away_team": "Time C",
                "away_goals": 1,
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
                "date": None,
                "time": None,
                "home_team_id": 4,
                "home_team": "Time D",
                "home_goals": None,
                "away_team_id": 1,
                "away_team": "Time A",
                "away_goals": None,
                "venue": None,
                "city": None,
                "state": None,
                "championship": "Brasileirão",
            },
        ]
    )


def create_validation_session():
    """Cria um SQLite em memória."""

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

    return session_factory()


# =============================================================================
# Normalização
# =============================================================================


def test_normalize_matches_dataframe():
    matches = create_validation_matches()

    normalized = (
        normalize_matches_dataframe(
            matches
        )
    )

    match = normalized[
        normalized[
            "match_id"
        ] == 101
    ].iloc[0]

    assert (
        match["date"]
        == "2026-01-10"
    )

    assert (
        match["time"]
        == "18:00"
    )

    future = normalized[
        normalized[
            "match_id"
        ] == 104
    ].iloc[0]

    assert future[
        "date"
    ] is None

    assert future[
        "time"
    ] is None


# =============================================================================
# Leitura
# =============================================================================


def test_load_matches_from_database():
    matches = create_validation_matches()

    with create_validation_session() as session:

        sync_database(
            session,
            matches,
        )

        session.commit()

        database_matches = (
            load_matches_from_database(
                session,
                season=2026,
            )
        )

        assert len(
            database_matches
        ) == 4

        match = database_matches[
            database_matches[
                "match_id"
            ] == 101
        ].iloc[0]

        assert (
            match[
                "home_team"
            ]
            == "Time A"
        )

        assert (
            match[
                "away_team"
            ]
            == "Time B"
        )


# =============================================================================
# Comparação perfeita
# =============================================================================


def test_identical_dataframes_match():
    matches = create_validation_matches()

    result = (
        compare_matches_dataframes(
            matches,
            matches.copy(),
        )
    )

    assert (
        result[
            "exact_match"
        ]
        is True
    )

    assert (
        result[
            "difference_count"
        ]
        == 0
    )


# =============================================================================
# Ausência
# =============================================================================


def test_detects_missing_database_match():
    matches = create_validation_matches()

    database_matches = (
        matches[
            matches[
                "match_id"
            ] != 104
        ].copy()
    )

    result = (
        compare_matches_dataframes(
            matches,
            database_matches,
        )
    )

    assert (
        result[
            "exact_match"
        ]
        is False
    )

    assert (
        result[
            "missing_in_database"
        ]
        == [
            104
        ]
    )


# =============================================================================
# Extra
# =============================================================================


def test_detects_extra_database_match():
    matches = create_validation_matches()

    extra_match = (
        matches.iloc[
            [0]
        ].copy()
    )

    extra_match[
        "match_id"
    ] = 999

    database_matches = pd.concat(
        [
            matches,
            extra_match,
        ],
        ignore_index=True,
    )

    result = (
        compare_matches_dataframes(
            matches,
            database_matches,
        )
    )

    assert (
        result[
            "exact_match"
        ]
        is False
    )

    assert (
        result[
            "extra_in_database"
        ]
        == [
            999
        ]
    )


# =============================================================================
# Divergência de campo
# =============================================================================


def test_detects_changed_score():
    matches = create_validation_matches()

    database_matches = (
        matches.copy()
    )

    database_matches.loc[
        database_matches[
            "match_id"
        ] == 101,
        "home_goals",
    ] = 5

    result = (
        compare_matches_dataframes(
            matches,
            database_matches,
        )
    )

    assert (
        result[
            "exact_match"
        ]
        is False
    )

    assert (
        result[
            "difference_count"
        ]
        == 1
    )

    difference = result[
        "differences"
    ][0]

    assert (
        difference[
            "match_id"
        ]
        == 101
    )

    assert (
        difference[
            "column"
        ]
        == "home_goals"
    )


# =============================================================================
# Validação integrada
# =============================================================================


def test_database_matches_csv_after_sync():
    matches = create_validation_matches()

    with create_validation_session() as session:

        sync_database(
            session,
            matches,
        )

        session.commit()

        result = (
            validate_database_against_matches(
                session,
                matches,
            )
        )

        assert (
            result[
                "season"
            ]
            == 2026
        )

        assert (
            result[
                "csv_count"
            ]
            == 4
        )

        assert (
            result[
                "database_count"
            ]
            == 4
        )

        assert (
            result[
                "exact_match"
            ]
            is True
        )