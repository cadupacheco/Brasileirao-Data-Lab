from pathlib import Path

from brasileirao_data_lab.scrapers.cbf import (
    parse_standings,
    resolve_next_opponents,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

HTML_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "cbf_serie_a_2026.html"
)


def load_html() -> str:
    return HTML_FILE.read_text(encoding="utf-8")


def get_standings() -> list[dict]:
    html = load_html()

    standings = parse_standings(html)

    return resolve_next_opponents(standings)


def test_standings_has_20_teams():
    standings = get_standings()

    assert len(standings) == 20


def test_positions_are_unique():
    standings = get_standings()

    positions = [
        team["position"]
        for team in standings
    ]

    assert len(positions) == len(set(positions))


def test_team_ids_are_unique():
    standings = get_standings()

    team_ids = [
        team["team_id"]
        for team in standings
    ]

    assert len(team_ids) == len(set(team_ids))


def test_points_are_consistent():
    standings = get_standings()

    for team in standings:
        expected_points = (
            team["wins"] * 3
            + team["draws"]
        )

        assert team["points"] == expected_points


def test_matches_are_consistent():
    standings = get_standings()

    for team in standings:
        expected_matches = (
            team["wins"]
            + team["draws"]
            + team["losses"]
        )

        assert team["matches"] == expected_matches


def test_goal_difference_is_consistent():
    standings = get_standings()

    for team in standings:
        expected_difference = (
            team["goals_for"]
            - team["goals_against"]
        )

        assert (
            team["goal_difference"]
            == expected_difference
        )


def test_next_opponents_exist():
    standings = get_standings()

    teams = {
        team["team"]
        for team in standings
    }

    for team in standings:
        assert team["next_opponent"] in teams