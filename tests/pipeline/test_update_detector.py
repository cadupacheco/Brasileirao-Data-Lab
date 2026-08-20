from __future__ import annotations

import pandas as pd
import pytest

from brasileirao_data_lab.pipelines.update_detector import (
    compare_match_snapshots,
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
    match_id: int = 1,
    status: str = "upcoming",
    home_goals: int | None = None,
    away_goals: int | None = None,
    date: str = "2026-08-20",
    time: str = "21:30",
) -> dict:
    result = None

    if status == "played":
        if home_goals > away_goals:
            result = "HOME"
        elif away_goals > home_goals:
            result = "AWAY"
        else:
            result = "DRAW"

    return {
        "season": 2026,
        "competition_id": 1260611,
        "round": 24,
        "match_id": match_id,
        "match_number": match_id,
        "group": "GRUPO ÚNICO",
        "date": date,
        "time": time,
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
        "status": status,
        "result": result,
    }


def dataframe(
    *matches: dict,
) -> pd.DataFrame:
    return pd.DataFrame(
        list(matches),
        columns=COLUMNS,
    )


def test_no_changes_returns_false():
    previous = dataframe(
        make_match()
    )
    current = dataframe(
        make_match()
    )

    result = compare_match_snapshots(
        previous,
        current,
    )

    assert result.has_changes is False
    assert result.total_changes == 0


def test_detects_newly_played_match():
    previous = dataframe(
        make_match(
            status="upcoming",
        )
    )
    current = dataframe(
        make_match(
            status="played",
            home_goals=2,
            away_goals=1,
        )
    )

    result = compare_match_snapshots(
        previous,
        current,
    )

    assert result.has_changes is True
    assert result.changed_match_ids == (1,)
    assert result.newly_played_match_ids == (1,)

    fields = (
        result
        .changed_matches[0]
        .changed_fields
    )

    assert "home_goals" in fields
    assert "away_goals" in fields
    assert "status" in fields
    assert "result" in fields


def test_detects_schedule_change():
    previous = dataframe(
        make_match(
            date="2026-08-20",
            time="21:30",
        )
    )
    current = dataframe(
        make_match(
            date="2026-08-21",
            time="19:00",
        )
    )

    result = compare_match_snapshots(
        previous,
        current,
    )

    assert result.changed_match_ids == (1,)
    assert (
        result
        .changed_matches[0]
        .changed_fields
        == ("date", "time")
    )


def test_detects_new_match_id():
    previous = dataframe(
        make_match(
            match_id=1,
        )
    )
    current = dataframe(
        make_match(
            match_id=1,
        ),
        make_match(
            match_id=2,
        ),
    )

    result = compare_match_snapshots(
        previous,
        current,
    )

    assert result.new_match_ids == (2,)


def test_detects_removed_match_id():
    previous = dataframe(
        make_match(
            match_id=1,
        ),
        make_match(
            match_id=2,
        ),
    )
    current = dataframe(
        make_match(
            match_id=1,
        )
    )

    result = compare_match_snapshots(
        previous,
        current,
    )

    assert result.removed_match_ids == (2,)


def test_nan_and_none_are_equal():
    previous_match = make_match()
    current_match = make_match()

    previous_match["home_goals"] = float("nan")
    current_match["home_goals"] = None

    result = compare_match_snapshots(
        dataframe(previous_match),
        dataframe(current_match),
    )

    assert result.has_changes is False


def test_rejects_duplicate_match_ids():
    previous = dataframe(
        make_match(
            match_id=1,
        )
    )
    current = dataframe(
        make_match(
            match_id=1,
        ),
        make_match(
            match_id=1,
        ),
    )

    with pytest.raises(
        ValueError,
        match="duplicados",
    ):
        compare_match_snapshots(
            previous,
            current,
        )
