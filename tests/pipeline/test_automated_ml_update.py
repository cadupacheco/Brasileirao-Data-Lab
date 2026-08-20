from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from brasileirao_data_lab.pipelines.automated_ml_update import (
    MLArtifacts,
    build_updated_history,
    get_artifact_targets,
    save_ml_artifacts_atomically,
    validate_current_season_snapshot,
)


COLUMNS = [
    "season",
    "competition_id",
    "round",
    "match_id",
    "match_number",
    "group",
    "date",
    "time",
    "home_team_id",
    "home_team",
    "home_goals",
    "away_team_id",
    "away_team",
    "away_goals",
    "venue",
    "city",
    "state",
    "championship",
    "status",
    "result",
]


def make_match(
    season: int,
    match_id: int,
    home_goals: int | None = None,
    away_goals: int | None = None,
) -> dict:

    played = (
        home_goals is not None
        and away_goals is not None
    )

    result = None

    if played:

        if home_goals > away_goals:
            result = "HOME"

        elif away_goals > home_goals:
            result = "AWAY"

        else:
            result = "DRAW"

    return {
        "season": season,
        "competition_id": (
            1260611
            if season == 2026
            else 12606
        ),
        "round": 1,
        "match_id": match_id,
        "match_number": match_id,
        "group": "GRUPO ÚNICO",
        "date": f"{season}-01-01",
        "time": "16:00",
        "home_team_id": 10,
        "home_team": "Time A",
        "home_goals": home_goals,
        "away_team_id": 20,
        "away_team": "Time B",
        "away_goals": away_goals,
        "venue": "Estádio Teste",
        "city": "São Paulo",
        "state": "SP",
        "championship": "Campeonato Brasileiro",
        "status": (
            "played"
            if played
            else "upcoming"
        ),
        "result": result,
    }


def dataframe(
    *matches: dict,
) -> pd.DataFrame:

    return pd.DataFrame(
        list(
            matches
        ),
        columns=COLUMNS,
    )


def test_validate_current_season_snapshot():

    current = dataframe(
        make_match(
            season=2026,
            match_id=1,
        ),
        make_match(
            season=2026,
            match_id=2,
        ),
    )

    validate_current_season_snapshot(
        dataframe=current,
        season=2026,
        expected_matches=2,
    )


def test_validate_current_season_rejects_wrong_count():

    current = dataframe(
        make_match(
            season=2026,
            match_id=1,
        )
    )

    with pytest.raises(
        ValueError,
        match="esperado 2 jogos",
    ):

        validate_current_season_snapshot(
            dataframe=current,
            season=2026,
            expected_matches=2,
        )


def test_build_updated_history_replaces_only_current_season():

    previous = dataframe(
        make_match(
            season=2025,
            match_id=100,
            home_goals=1,
            away_goals=0,
        ),
        make_match(
            season=2026,
            match_id=200,
        ),
        make_match(
            season=2026,
            match_id=201,
        ),
    )

    current = dataframe(
        make_match(
            season=2026,
            match_id=200,
            home_goals=2,
            away_goals=1,
        ),
        make_match(
            season=2026,
            match_id=201,
        ),
    )

    updated = build_updated_history(
        previous_history=previous,
        current_season=current,
        season=2026,
        expected_matches=2,
    )

    assert len(
        updated
    ) == 3

    match_2025 = (
        updated[
            updated[
                "match_id"
            ] == 100
        ]
        .iloc[
            0
        ]
    )

    assert (
        match_2025[
            "home_goals"
        ]
        == 1
    )

    match_2026 = (
        updated[
            updated[
                "match_id"
            ] == 200
        ]
        .iloc[
            0
        ]
    )

    assert (
        match_2026[
            "home_goals"
        ]
        == 2
    )

    assert (
        match_2026[
            "away_goals"
        ]
        == 1
    )

    assert (
        match_2026[
            "status"
        ]
        == "played"
    )


def test_atomic_save_writes_all_artifacts(
    tmp_path: Path,
):

    history = pd.DataFrame(
        {
            "value": [
                "history",
            ],
        }
    )

    features = pd.DataFrame(
        {
            "value": [
                "features",
            ],
        }
    )

    predictions = pd.DataFrame(
        {
            "value": [
                "predictions",
            ],
        }
    )

    simulation = pd.DataFrame(
        {
            "value": [
                "simulation",
            ],
        }
    )

    artifacts = MLArtifacts(
        history=history,
        features=features,
        predictions=predictions,
        simulation=simulation,
    )

    targets = save_ml_artifacts_atomically(
        artifacts=artifacts,
        output_dir=tmp_path,
    )

    expected_targets = (
        get_artifact_targets(
            output_dir=tmp_path
        )
    )

    assert (
        targets
        == expected_targets
    )

    assert (
        pd.read_csv(
            targets[
                "history"
            ]
        )[
            "value"
        ].iloc[
            0
        ]
        == "history"
    )

    assert (
        pd.read_csv(
            targets[
                "features"
            ]
        )[
            "value"
        ].iloc[
            0
        ]
        == "features"
    )

    assert (
        pd.read_csv(
            targets[
                "predictions"
            ]
        )[
            "value"
        ].iloc[
            0
        ]
        == "predictions"
    )

    assert (
        pd.read_csv(
            targets[
                "simulation"
            ]
        )[
            "value"
        ].iloc[
            0
        ]
        == "simulation"
    )