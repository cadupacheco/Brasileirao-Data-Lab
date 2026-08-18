import pandas as pd
import pytest

from brasileirao_data_lab.analytics.championship import (
    add_match_result,
    compare_with_official_standings,
    get_away_ranking,
    get_championship_summary,
    get_future_matches,
    get_home_away_stats,
    get_home_ranking,
    get_played_matches,
    get_recent_form_table,
    get_team_recent_matches,
    get_team_stats,
)


def create_sample_matches() -> pd.DataFrame:
    """Cria um pequeno campeonato para os testes."""

    return pd.DataFrame(
        [
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
                "round": 2,
                "date": "2026-01-17",
                "time": "18:00",
                "home_team_id": 3,
                "home_team": "Time C",
                "away_team_id": 1,
                "away_team": "Time A",
                "home_goals": 1,
                "away_goals": 1,
            },
            {
                "match_id": 103,
                "match_number": 3,
                "round": 3,
                "date": "2026-01-24",
                "time": "18:00",
                "home_team_id": 2,
                "home_team": "Time B",
                "away_team_id": 3,
                "away_team": "Time C",
                "home_goals": 0,
                "away_goals": 3,
            },
            {
                "match_id": 104,
                "match_number": 4,
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
        ]
    )


def create_sample_official_standings() -> pd.DataFrame:
    """Cria uma classificação oficial fictícia."""

    return pd.DataFrame(
        [
            {
                "position": 1,
                "team_id": 3,
                "team": "Time C",
                "matches": 2,
                "wins": 1,
                "draws": 1,
                "losses": 0,
                "goals_for": 4,
                "goals_against": 1,
                "goal_difference": 3,
                "points": 4,
            },
            {
                "position": 2,
                "team_id": 1,
                "team": "Time A",
                "matches": 2,
                "wins": 1,
                "draws": 1,
                "losses": 0,
                "goals_for": 3,
                "goals_against": 1,
                "goal_difference": 2,
                "points": 4,
            },
            {
                "position": 3,
                "team_id": 2,
                "team": "Time B",
                "matches": 2,
                "wins": 0,
                "draws": 0,
                "losses": 2,
                "goals_for": 0,
                "goals_against": 5,
                "goal_difference": -5,
                "points": 0,
            },
        ]
    )


# =============================================================================
# Jogos realizados e futuros
# =============================================================================


def test_played_matches():
    matches = create_sample_matches()

    played = get_played_matches(
        matches
    )

    assert len(played) == 3


def test_future_matches():
    matches = create_sample_matches()

    future = get_future_matches(
        matches
    )

    assert len(future) == 1


# =============================================================================
# Resultado
# =============================================================================


def test_match_results():
    matches = create_sample_matches()

    played = get_played_matches(
        matches
    )

    played = add_match_result(
        played
    )

    assert list(
        played["result"]
    ) == [
        "H",
        "D",
        "A",
    ]


# =============================================================================
# Resumo do campeonato
# =============================================================================


def test_championship_summary():
    matches = create_sample_matches()

    summary = get_championship_summary(
        matches
    )

    assert summary["total_matches"] == 4
    assert summary["played_matches"] == 3
    assert summary["future_matches"] == 1

    assert summary["total_goals"] == 7

    assert summary["home_wins"] == 1
    assert summary["draws"] == 1
    assert summary["away_wins"] == 1


# =============================================================================
# Estatísticas gerais por clube
# =============================================================================


def test_team_stats():
    matches = create_sample_matches()

    stats = get_team_stats(
        matches
    )

    team_a = stats[
        stats["team_id"] == 1
    ].iloc[0]

    assert team_a["team"] == "Time A"

    assert team_a["matches"] == 2
    assert team_a["wins"] == 1
    assert team_a["draws"] == 1
    assert team_a["losses"] == 0

    assert team_a["goals_for"] == 3
    assert team_a["goals_against"] == 1

    assert team_a["goal_difference"] == 2
    assert team_a["points"] == 4


def test_team_points_are_consistent():
    matches = create_sample_matches()

    stats = get_team_stats(
        matches
    )

    for _, team in stats.iterrows():

        expected_points = (
            team["wins"] * 3
            + team["draws"]
        )

        assert (
            team["points"]
            == expected_points
        )


# =============================================================================
# Casa x fora
# =============================================================================


def test_home_away_stats():
    matches = create_sample_matches()

    stats = get_home_away_stats(
        matches
    )

    team_a = stats[
        stats["team_id"] == 1
    ].iloc[0]

    assert team_a["home_matches"] == 1
    assert team_a["home_wins"] == 1
    assert team_a["home_draws"] == 0
    assert team_a["home_losses"] == 0
    assert team_a["home_points"] == 3
    assert team_a["home_goals_for"] == 2
    assert team_a["home_goals_against"] == 0
    assert team_a["home_performance_pct"] == 100

    assert team_a["away_matches"] == 1
    assert team_a["away_wins"] == 0
    assert team_a["away_draws"] == 1
    assert team_a["away_losses"] == 0
    assert team_a["away_points"] == 1
    assert team_a["away_goals_for"] == 1
    assert team_a["away_goals_against"] == 1


def test_home_ranking():
    matches = create_sample_matches()

    ranking = get_home_ranking(
        matches
    )

    assert (
        ranking.iloc[0]["team"]
        == "Time A"
    )

    assert (
        ranking.iloc[0]["home_points"]
        == 3
    )


def test_away_ranking():
    matches = create_sample_matches()

    ranking = get_away_ranking(
        matches
    )

    assert (
        ranking.iloc[0]["team"]
        == "Time C"
    )

    assert (
        ranking.iloc[0]["away_points"]
        == 3
    )


# =============================================================================
# Forma recente
# =============================================================================


def test_team_recent_matches():
    matches = create_sample_matches()

    recent = get_team_recent_matches(
        matches,
        team_id=1,
        last_n=5,
    )

    assert len(recent) == 2

    assert recent[0]["result"] == "V"
    assert recent[1]["result"] == "E"

    assert recent[0]["opponent"] == "Time B"
    assert recent[1]["opponent"] == "Time C"


def test_team_recent_matches_respects_limit():
    matches = create_sample_matches()

    recent = get_team_recent_matches(
        matches,
        team_id=1,
        last_n=1,
    )

    assert len(recent) == 1

    assert recent[0]["result"] == "E"


def test_recent_form_table():
    matches = create_sample_matches()

    form = get_recent_form_table(
        matches,
        last_n=5,
    )

    team_a = form[
        form["team_id"] == 1
    ].iloc[0]

    assert team_a["recent_matches"] == 2
    assert team_a["recent_wins"] == 1
    assert team_a["recent_draws"] == 1
    assert team_a["recent_losses"] == 0

    assert team_a["recent_points"] == 4
    assert team_a["recent_goals_for"] == 3
    assert team_a["recent_goals_against"] == 1

    assert team_a["recent_form"] == "V E"


def test_recent_form_ranking():
    matches = create_sample_matches()

    form = get_recent_form_table(
        matches,
        last_n=5,
    )

    assert (
        form.iloc[0]["team"]
        == "Time C"
    )

    assert (
        form.iloc[0]["recent_points"]
        == 4
    )


def test_invalid_recent_form_limit():
    matches = create_sample_matches()

    with pytest.raises(ValueError):
        get_team_recent_matches(
            matches,
            team_id=1,
            last_n=0,
        )

    with pytest.raises(ValueError):
        get_recent_form_table(
            matches,
            last_n=0,
        )


# =============================================================================
# Comparação com classificação oficial
# =============================================================================


def test_comparison_with_official_standings():
    matches = create_sample_matches()

    official = (
        create_sample_official_standings()
    )

    comparison = (
        compare_with_official_standings(
            matches,
            official,
        )
    )

    assert len(comparison) == 3

    assert (
        comparison[
            "all_stats_match"
        ].all()
    )

    assert (
        comparison[
            "position_match"
        ].all()
    )


def test_comparison_detects_difference():
    matches = create_sample_matches()

    official = (
        create_sample_official_standings()
    )

    official.loc[
        official["team_id"] == 2,
        "points",
    ] = 1

    comparison = (
        compare_with_official_standings(
            matches,
            official,
        )
    )

    team_b = comparison[
        comparison["team_id"] == 2
    ].iloc[0]

    assert not bool(
        team_b["points_match"]
    )

    assert not bool(
        team_b["all_stats_match"]
    )