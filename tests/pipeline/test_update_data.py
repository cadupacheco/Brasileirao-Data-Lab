from __future__ import annotations

import pandas as pd
import pytest

import brasileirao_data_lab.pipelines.update_data as update_data_module

from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.database.session import (
    create_database_engine,
    create_session_factory,
)
from brasileirao_data_lab.database.sync import (
    get_database_counts,
)
from brasileirao_data_lab.pipelines.update_data import (
    raise_for_database_validation,
    sync_and_validate_database,
)


# =============================================================================
# Dataset
# =============================================================================


def create_pipeline_matches() -> pd.DataFrame:
    """
    Dataset mínimo para testar a integração
    Pipeline -> Database.

    Possui uma rodada realizada
    e uma rodada futura.
    """

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
                "round": 2,
                "match_id": 102,
                "match_number": 2,
                "group": "A",
                "date": None,
                "time": None,
                "home_team_id": 2,
                "home_team": "Time B",
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


def create_pipeline_database():
    """Cria um SQLite isolado em memória."""

    database_engine = create_database_engine(
        "sqlite+pysqlite:///:memory:"
    )

    init_database(
        database_engine
    )

    session_factory = create_session_factory(
        database_engine
    )

    return (
        database_engine,
        session_factory,
    )


# =============================================================================
# Validação
# =============================================================================


def test_database_validation_accepts_exact_match():
    validation_result = {
        "exact_match": True,
        "missing_in_database": [],
        "extra_in_database": [],
        "difference_count": 0,
    }

    raise_for_database_validation(
        validation_result
    )


def test_database_validation_rejects_difference():
    validation_result = {
        "exact_match": False,
        "missing_in_database": [
            101
        ],
        "extra_in_database": [],
        "difference_count": 2,
    }

    with pytest.raises(
        ValueError,
        match="Validação CSV x Database falhou",
    ):

        raise_for_database_validation(
            validation_result
        )


# =============================================================================
# Integração
# =============================================================================


def test_pipeline_syncs_and_validates_database():
    matches = create_pipeline_matches()

    (
        database_engine,
        session_factory,
    ) = create_pipeline_database()

    sync_result, validation_result = (
        sync_and_validate_database(
            matches,
            database_engine=database_engine,
            session_factory=session_factory,
        )
    )

    assert (
        validation_result[
            "exact_match"
        ]
        is True
    )

    assert (
        validation_result[
            "difference_count"
        ]
        == 0
    )

    assert sync_result[
        "counts"
    ] == {
        "teams": 2,
        "matches": 2,
        "standings_snapshots": 2,
    }


def test_pipeline_database_sync_is_idempotent():
    matches = create_pipeline_matches()

    (
        database_engine,
        session_factory,
    ) = create_pipeline_database()

    first_sync, first_validation = (
        sync_and_validate_database(
            matches,
            database_engine=database_engine,
            session_factory=session_factory,
        )
    )

    second_sync, second_validation = (
        sync_and_validate_database(
            matches,
            database_engine=database_engine,
            session_factory=session_factory,
        )
    )

    assert (
        first_validation[
            "exact_match"
        ]
        is True
    )

    assert (
        second_validation[
            "exact_match"
        ]
        is True
    )

    assert (
        first_sync[
            "counts"
        ]
        == second_sync[
            "counts"
        ]
    )

    assert (
        second_sync[
            "teams"
        ]["inserted"]
        == 0
    )

    assert (
        second_sync[
            "matches"
        ]["inserted"]
        == 0
    )

    assert (
        second_sync[
            "standings_snapshots"
        ]["inserted"]
        == 0
    )


# =============================================================================
# Rollback
# =============================================================================


def test_pipeline_rolls_back_when_database_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Se a validação CSV x Database falhar,
    nenhum dado parcial deve permanecer salvo.
    """

    matches = create_pipeline_matches()

    (
        database_engine,
        session_factory,
    ) = create_pipeline_database()

    def fake_validation(
        session,
        csv_matches,
    ):
        del session
        del csv_matches

        return {
            "exact_match": False,
            "csv_count": 2,
            "database_count": 2,
            "common_count": 2,
            "missing_in_database": [],
            "extra_in_database": [],
            "differences": [
                {
                    "match_id": 101,
                    "column": "home_goals",
                    "csv_value": 2,
                    "database_value": 99,
                }
            ],
            "difference_count": 1,
            "season": 2026,
        }

    monkeypatch.setattr(
        update_data_module,
        "validate_database_against_matches",
        fake_validation,
    )

    with pytest.raises(
        ValueError,
        match="Validação CSV x Database falhou",
    ):

        sync_and_validate_database(
            matches,
            database_engine=database_engine,
            session_factory=session_factory,
        )

    with session_factory() as session:

        counts = get_database_counts(
            session
        )

    assert counts == {
        "teams": 0,
        "matches": 0,
        "standings_snapshots": 0,
    }