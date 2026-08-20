from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from brasileirao_data_lab.pipelines.automated_project_update import (
    PROCESSED_MATCH_COLUMNS,
    build_database_file,
    build_processed_matches_dataframe,
)


def make_match(
    match_id: int,
    home_goals: int | None = None,
    away_goals: int | None = None,
) -> dict:

    played = (
        home_goals is not None
        and away_goals is not None
    )

    return {
        "season": 2026,
        "competition_id": 1260611,
        "round": 1,
        "match_id": match_id,
        "match_number": match_id,
        "group": "GRUPO ÚNICO",
        "date": "2026-01-01",
        "time": "16:00",
        "home_team_id": (
            100
            + match_id
        ),
        "home_team": (
            f"Mandante {match_id}"
        ),
        "home_goals": (
            home_goals
        ),
        "away_team_id": (
            200
            + match_id
        ),
        "away_team": (
            f"Visitante {match_id}"
        ),
        "away_goals": (
            away_goals
        ),
        "venue": "Estádio Teste",
        "city": "São Paulo",
        "state": "SP",
        "championship": (
            "Campeonato Brasileiro"
        ),
        "status": (
            "played"
            if played
            else "upcoming"
        ),
        "result": (
            "HOME"
            if (
                played
                and home_goals
                > away_goals
            )
            else (
                "DRAW"
                if (
                    played
                    and home_goals
                    == away_goals
                )
                else (
                    "AWAY"
                    if played
                    else None
                )
            )
        ),
    }


def dataframe(
    *matches: dict,
) -> pd.DataFrame:

    return pd.DataFrame(
        list(
            matches
        )
    )


def test_build_processed_matches_dataframe():

    source = dataframe(
        make_match(
            match_id=2,
        ),
        make_match(
            match_id=1,
            home_goals=2,
            away_goals=1,
        ),
    )

    result = (
        build_processed_matches_dataframe(
            current_season=source,
            season=2026,
            expected_matches=2,
        )
    )

    assert len(
        result
    ) == 2

    assert list(
        result.columns
    ) == PROCESSED_MATCH_COLUMNS

    assert list(
        result[
            "match_id"
        ]
    ) == [
        1,
        2,
    ]

    assert (
        "status"
        not in result.columns
    )

    assert (
        "result"
        not in result.columns
    )

    assert (
        "competition_id"
        not in result.columns
    )


def test_build_processed_matches_rejects_wrong_count():

    source = dataframe(
        make_match(
            match_id=1,
        )
    )

    with pytest.raises(
        ValueError,
        match="esperado 2 jogos",
    ):

        build_processed_matches_dataframe(
            current_season=source,
            season=2026,
            expected_matches=2,
        )


def test_build_database_file(
    tmp_path: Path,
):

    matches = dataframe(
        make_match(
            match_id=1,
            home_goals=2,
            away_goals=0,
        ),
        make_match(
            match_id=2,
        ),
    )

    processed = (
        build_processed_matches_dataframe(
            current_season=matches,
            season=2026,
            expected_matches=2,
        )
    )

    database_file = (
        tmp_path
        / "test_brasileirao.db"
    )

    result = build_database_file(
        matches=processed,
        database_file=database_file,
    )

    assert (
        result
        == database_file
    )

    assert database_file.exists()

    assert (
        database_file.stat().st_size
        > 0
    )