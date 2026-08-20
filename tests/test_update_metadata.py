from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from brasileirao_data_lab.update_metadata import (
    UpdateMetadata,
    build_update_metadata,
    load_update_metadata,
    metadata_to_dict,
    save_update_metadata,
)


def make_matches() -> pd.DataFrame:
    """
    Dataset mínimo para testar metadata.
    """

    return pd.DataFrame(
        [
            {
                "season": 2026,
                "match_id": 1,
                "status": "played",
            },
            {
                "season": 2026,
                "match_id": 2,
                "status": "played",
            },
            {
                "season": 2026,
                "match_id": 3,
                "status": "upcoming",
            },
            {
                "season": 2025,
                "match_id": 4,
                "status": "played",
            },
        ]
    )


def test_build_update_metadata():

    matches = make_matches()

    metadata = build_update_metadata(
        matches=matches,
        season=2026,
        synced_at_utc=(
            "2026-08-20T12:01:55Z"
        ),
    )

    assert metadata.season == 2026
    assert metadata.source == "CBF"
    assert metadata.status == "up_to_date"

    assert (
        metadata.last_sync_at_utc
        == "2026-08-20T12:01:55Z"
    )

    assert metadata.total_matches == 3
    assert metadata.played_matches == 2
    assert metadata.future_matches == 1

    assert (
        metadata.automation_enabled
        is True
    )

    assert metadata.checks_per_day == 4


def test_metadata_to_dict():

    metadata = UpdateMetadata(
        season=2026,
        source="CBF",
        status="up_to_date",
        last_sync_at_utc=(
            "2026-08-20T12:01:55Z"
        ),
        total_matches=380,
        played_matches=225,
        future_matches=155,
        automation_enabled=True,
        checks_per_day=4,
    )

    result = metadata_to_dict(
        metadata
    )

    assert result == {
        "season": 2026,
        "source": "CBF",
        "status": "up_to_date",
        "last_sync_at_utc": (
            "2026-08-20T12:01:55Z"
        ),
        "total_matches": 380,
        "played_matches": 225,
        "future_matches": 155,
        "automation_enabled": True,
        "checks_per_day": 4,
    }


def test_build_update_metadata_rejects_invalid_status():

    matches = pd.DataFrame(
        [
            {
                "season": 2026,
                "status": "banana",
            },
        ]
    )

    with pytest.raises(
        ValueError,
        match="Status de partida inválido",
    ):

        build_update_metadata(
            matches=matches,
            season=2026,
        )


def test_save_and_load_update_metadata(
    tmp_path: Path,
):

    metadata = UpdateMetadata(
        season=2026,
        source="CBF",
        status="up_to_date",
        last_sync_at_utc=(
            "2026-08-20T12:01:55Z"
        ),
        total_matches=380,
        played_matches=225,
        future_matches=155,
        automation_enabled=True,
        checks_per_day=4,
    )

    output_file = (
        tmp_path
        / "update_metadata.json"
    )

    result = save_update_metadata(
        metadata=metadata,
        path=output_file,
    )

    assert result == output_file
    assert output_file.exists()

    loaded = load_update_metadata(
        output_file
    )

    assert loaded == metadata


def test_build_update_metadata_rejects_empty_dataframe():

    with pytest.raises(
        ValueError,
        match="dataset vazio",
    ):

        build_update_metadata(
            matches=pd.DataFrame(),
            season=2026,
        )