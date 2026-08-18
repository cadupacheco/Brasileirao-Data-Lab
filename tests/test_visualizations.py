from pathlib import Path

import pandas as pd
import pytest

from brasileirao_data_lab.analytics.visualizations import (
    generate_all_charts,
    plot_home_away_performance,
    plot_points_evolution,
    plot_position_evolution,
)


def create_visualization_matches() -> pd.DataFrame:
    """Cria dados fictícios para testar os gráficos."""

    return pd.DataFrame(
        [
            # Rodada 1
            {
                "match_id": 101,
                "match_number": 1,
                "round": 1,
                "date": "2026-01-10",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "away_team_id": 2,
                "away_team": "Time B",
                "home_goals": 2,
                "away_goals": 0,
            },
            {
                "match_id": 102,
                "match_number": 2,
                "round": 1,
                "date": "2026-01-10",
                "time": "20:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "away_team_id": 4,
                "away_team": "Time D",
                "home_goals": 1,
                "away_goals": 0,
            },

            # Rodada 2
            {
                "match_id": 103,
                "match_number": 3,
                "round": 2,
                "date": "2026-01-17",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": 1,
                "away_goals": 0,
            },
            {
                "match_id": 104,
                "match_number": 4,
                "round": 2,
                "date": "2026-01-17",
                "time": "20:00",
                "home_team_id": 4,
                "home_team": "Time D",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": 0,
                "away_goals": 0,
            },

            # Rodada 3
            {
                "match_id": 105,
                "match_number": 5,
                "round": 3,
                "date": "2026-01-24",
                "time": "18:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": 3,
                "away_goals": 0,
            },
            {
                "match_id": 106,
                "match_number": 6,
                "round": 3,
                "date": "2026-01-24",
                "time": "20:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 4,
                "away_team": "Time D",
                "home_goals": 2,
                "away_goals": 0,
            },

            # Rodada 4 futura
            {
                "match_id": 107,
                "match_number": 7,
                "round": 4,
                "date": "2026-01-31",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": None,
                "away_goals": None,
            },
            {
                "match_id": 108,
                "match_number": 8,
                "round": 4,
                "date": "2026-01-31",
                "time": "20:00",
                "home_team_id": 4,
                "home_team": "Time D",
                "away_team_id": 2,
                "away_team": "Time B",
                "home_goals": None,
                "away_goals": None,
            },
        ]
    )


# =============================================================================
# Evolução de posição
# =============================================================================


def test_position_evolution_creates_file(
    tmp_path: Path,
):
    matches = (
        create_visualization_matches()
    )

    output_file = plot_position_evolution(
        matches,
        top_n=4,
        output_dir=tmp_path,
    )

    assert output_file.exists()

    assert (
        output_file.name
        == "position_evolution.png"
    )

    assert (
        output_file.stat().st_size
        > 0
    )


# =============================================================================
# Evolução de pontos
# =============================================================================


def test_points_evolution_creates_file(
    tmp_path: Path,
):
    matches = (
        create_visualization_matches()
    )

    output_file = plot_points_evolution(
        matches,
        top_n=4,
        output_dir=tmp_path,
    )

    assert output_file.exists()

    assert (
        output_file.name
        == "points_evolution.png"
    )

    assert (
        output_file.stat().st_size
        > 0
    )


# =============================================================================
# Casa x fora
# =============================================================================


def test_home_away_performance_creates_file(
    tmp_path: Path,
):
    matches = (
        create_visualization_matches()
    )

    output_file = (
        plot_home_away_performance(
            matches,
            top_n=4,
            output_dir=tmp_path,
        )
    )

    assert output_file.exists()

    assert (
        output_file.name
        == "home_away_performance.png"
    )

    assert (
        output_file.stat().st_size
        > 0
    )


# =============================================================================
# Geração completa
# =============================================================================


def test_generate_all_charts(
    tmp_path: Path,
):
    matches = (
        create_visualization_matches()
    )

    files = generate_all_charts(
        matches=matches,
        output_dir=tmp_path,
    )

    assert len(files) == 3

    for file_path in files:

        assert file_path.exists()

        assert (
            file_path.stat().st_size
            > 0
        )


# =============================================================================
# Validação
# =============================================================================


def test_invalid_top_n(
    tmp_path: Path,
):
    matches = (
        create_visualization_matches()
    )

    with pytest.raises(
        ValueError
    ):
        plot_position_evolution(
            matches,
            top_n=0,
            output_dir=tmp_path,
        )

    with pytest.raises(
        ValueError
    ):
        plot_points_evolution(
            matches,
            top_n=0,
            output_dir=tmp_path,
        )

    with pytest.raises(
        ValueError
    ):
        plot_home_away_performance(
            matches,
            top_n=0,
            output_dir=tmp_path,
        )