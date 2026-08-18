from pathlib import Path

import pandas as pd
import pytest

from brasileirao_data_lab.analytics.team_visualization import (
    plot_team_report,
    resolve_output_path,
    slugify_team_name,
)


def create_team_visualization_matches() -> pd.DataFrame:
    """Dataset fictício para testar o painel."""

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
                "venue": "Estádio A",
                "city": "Cidade A",
                "state": "SP",
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
                "venue": "Estádio C",
                "city": "Cidade C",
                "state": "RJ",
            },

            # Rodada 2
            {
                "match_id": 103,
                "match_number": 3,
                "round": 2,
                "date": "2026-01-17",
                "time": "18:00",
                "home_team_id": 4,
                "home_team": "Time D",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": 1,
                "away_goals": 1,
                "venue": "Estádio D",
                "city": "Cidade D",
                "state": "MG",
            },
            {
                "match_id": 104,
                "match_number": 4,
                "round": 2,
                "date": "2026-01-17",
                "time": "20:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": 0,
                "away_goals": 1,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
            },

            # Rodada 3
            {
                "match_id": 105,
                "match_number": 5,
                "round": 3,
                "date": "2026-01-24",
                "time": "18:00",
                "home_team_id": 1,
                "home_team": "Time A",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": 3,
                "away_goals": 1,
                "venue": "Estádio A",
                "city": "Cidade A",
                "state": "SP",
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
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
            },

            # Próximo jogo
            {
                "match_id": 107,
                "match_number": 7,
                "round": 4,
                "date": "2026-01-31",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": None,
                "away_goals": None,
                "venue": "Estádio B",
                "city": "Cidade B",
                "state": "RS",
            },
            {
                "match_id": 108,
                "match_number": 8,
                "round": 4,
                "date": "2026-01-31",
                "time": "20:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "away_team_id": 4,
                "away_team": "Time D",
                "home_goals": None,
                "away_goals": None,
                "venue": "Estádio C",
                "city": "Cidade C",
                "state": "RJ",
            },
        ]
    )


# =============================================================================
# Slug
# =============================================================================


def test_slugify_team_name():
    assert (
        slugify_team_name(
            "Atlético Mineiro"
        )
        == "atletico_mineiro"
    )

    assert (
        slugify_team_name(
            "Red Bull Bragantino"
        )
        == "red_bull_bragantino"
    )


# =============================================================================
# Caminho
# =============================================================================


def test_resolve_output_path(
    tmp_path: Path,
):
    output_file = resolve_output_path(
        "Atlético Mineiro",
        output_dir=tmp_path,
    )

    assert (
        output_file.name
        == "atletico_mineiro_report.png"
    )

    assert (
        output_file.parent
        == tmp_path
    )


# =============================================================================
# Geração
# =============================================================================


def test_plot_team_report_creates_file(
    tmp_path: Path,
):
    matches = (
        create_team_visualization_matches()
    )

    output_file = plot_team_report(
        matches,
        team_id=1,
        output_dir=tmp_path,
    )

    assert (
        output_file.exists()
    )

    assert (
        output_file.stat().st_size
        > 0
    )

    assert (
        output_file.name
        == "time_a_report.png"
    )


def test_plot_team_report_is_png(
    tmp_path: Path,
):
    matches = (
        create_team_visualization_matches()
    )

    output_file = plot_team_report(
        matches,
        team_id=1,
        output_dir=tmp_path,
    )

    assert (
        output_file.suffix
        == ".png"
    )


# =============================================================================
# Erros
# =============================================================================


def test_invalid_team_id(
    tmp_path: Path,
):
    matches = (
        create_team_visualization_matches()
    )

    with pytest.raises(
        ValueError
    ):
        plot_team_report(
            matches,
            team_id=999,
            output_dir=tmp_path,
        )