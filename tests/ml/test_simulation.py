from __future__ import annotations

import numpy as np
import pandas as pd

from brasileirao_data_lab.ml.simulation import (
    build_current_standings,
    build_score_pools,
    rank_simulations,
)


def build_history() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "season": 2026,
                "home_team": "Palmeiras",
                "home_goals": 2,
                "away_team": "Flamengo",
                "away_goals": 1,
                "status": "played",
                "result": "HOME",
            },
            {
                "season": 2026,
                "home_team": "Flamengo",
                "home_goals": 0,
                "away_team": "Palmeiras",
                "away_goals": 0,
                "status": "played",
                "result": "DRAW",
            },
            {
                "season": 2026,
                "home_team": "Palmeiras",
                "home_goals": None,
                "away_team": "Flamengo",
                "away_goals": None,
                "status": "upcoming",
                "result": None,
            },
        ]
    )


def test_current_standings_uses_only_played_matches():
    standings = build_current_standings(
        history=build_history(),
        season=2026,
    )

    by_key = {
        team.team_key: team
        for team in standings
    }

    palmeiras = by_key[
        "palmeiras"
    ]

    flamengo = by_key[
        "flamengo"
    ]

    assert palmeiras.points == 4
    assert palmeiras.wins == 1
    assert palmeiras.goals_for == 2
    assert palmeiras.goals_against == 1

    assert flamengo.points == 1
    assert flamengo.wins == 0


def test_score_pools_keep_result_categories():
    pools = build_score_pools(
        pd.DataFrame(
            [
                {
                    "status": "played",
                    "result": "HOME",
                    "home_goals": 2,
                    "away_goals": 0,
                },
                {
                    "status": "played",
                    "result": "DRAW",
                    "home_goals": 1,
                    "away_goals": 1,
                },
                {
                    "status": "played",
                    "result": "AWAY",
                    "home_goals": 0,
                    "away_goals": 3,
                },
            ]
        )
    )

    assert np.all(
        pools.home_wins[
            :,
            0
        ]
        > pools.home_wins[
            :,
            1
        ]
    )

    assert np.all(
        pools.draws[
            :,
            0
        ]
        == pools.draws[
            :,
            1
        ]
    )

    assert np.all(
        pools.away_wins[
            :,
            0
        ]
        < pools.away_wins[
            :,
            1
        ]
    )


def test_rank_simulations_prioritizes_points_then_wins():
    points = np.array(
        [
            [
                70,
                68,
                60,
            ],
            [
                65,
                65,
                50,
            ],
        ],
        dtype=np.int16,
    )

    wins = np.array(
        [
            [
                20,
                19,
                15,
            ],
            [
                18,
                19,
                10,
            ],
        ],
        dtype=np.int16,
    )

    goals_for = np.array(
        [
            [
                60,
                58,
                50,
            ],
            [
                55,
                54,
                40,
            ],
        ],
        dtype=np.int16,
    )

    goals_against = np.array(
        [
            [
                30,
                32,
                40,
            ],
            [
                30,
                30,
                45,
            ],
        ],
        dtype=np.int16,
    )

    rng = np.random.default_rng(
        42
    )

    positions = rank_simulations(
        points=points,
        wins=wins,
        goals_for=goals_for,
        goals_against=goals_against,
        rng=rng,
    )

    assert positions[
        0,
        0
    ] == 1

    assert positions[
        1,
        1
    ] == 1