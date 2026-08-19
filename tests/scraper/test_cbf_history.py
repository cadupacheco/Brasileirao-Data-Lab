from pathlib import Path

import pandas as pd
import pytest

from brasileirao_data_lab.scrapers.cbf_history import (
    SEASON_COMPETITION_IDS,
    build_history_dataframe,
    get_match_result,
    get_match_status,
    parse_location,
    parse_match_date,
    parse_round_matches,
    validate_history_dataframe,
    validate_season_matches,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

HISTORY_FILE = (
    PROJECT_ROOT
    / "data"
    / "ml"
    / "matches_history.csv"
)


# =============================================================================
# Fixtures auxiliares
# =============================================================================


def completed_match_payload():
    return {
        "jogos": [
            {
                "grupo": "GRUPO ÚNICO",
                "jogo": [
                    {
                        "id_jogo": "817955",
                        "num_jogo": "1",
                        "rodada": "1",
                        "grupo": "GRUPO ÚNICO",
                        "mandante": {
                            "id": "20010",
                            "nome": "Cuiabá",
                            "gols": "2",
                        },
                        "visitante": {
                            "id": "20020",
                            "nome": "Juventude",
                            "gols": "2",
                        },
                        "local": (
                            "Arena Pantanal - "
                            "Cuiaba - MT"
                        ),
                        "campeonato": (
                            "Campeonato Brasileiro"
                        ),
                        "data": " 29/05/2021",
                        "hora": "19:00",
                    }
                ],
            }
        ],
    }


def future_match_payload():
    return {
        "jogos": [
            {
                "grupo": "GRUPO ÚNICO",
                "jogo": [
                    {
                        "id_jogo": "999999",
                        "num_jogo": "250",
                        "rodada": "25",
                        "grupo": "GRUPO ÚNICO",
                        "mandante": {
                            "id": "20001",
                            "nome": "Mandante",
                            "gols": None,
                        },
                        "visitante": {
                            "id": "20002",
                            "nome": "Visitante",
                            "gols": None,
                        },
                        "local": (
                            "Estádio Teste - "
                            "Cidade Teste - SP"
                        ),
                        "campeonato": (
                            "Campeonato Brasileiro"
                        ),
                        "data": "A Definir",
                        "hora": "A Definir",
                    }
                ],
            }
        ],
    }


def load_history_dataframe() -> pd.DataFrame:
    """
    Carrega o snapshot histórico local.

    Em ambientes de CI o CSV pode não existir.
    Nesse caso, somente os testes dependentes
    do snapshot são ignorados.
    """

    if not HISTORY_FILE.exists():
        pytest.skip(
            "Snapshot histórico não disponível. "
            "Execute "
            "'python scripts/collect_cbf_history.py' "
            "para gerar o arquivo localmente."
        )

    return pd.read_csv(
        HISTORY_FILE
    )


# =============================================================================
# Configuração histórica
# =============================================================================


def test_season_competition_ids_are_configured():
    assert SEASON_COMPETITION_IDS == {
        2021: 12487,
        2022: 12518,
        2023: 12555,
        2024: 12584,
        2025: 12606,
        2026: 1260611,
    }


# =============================================================================
# Resultado e status
# =============================================================================


@pytest.mark.parametrize(
    (
        "home_goals",
        "away_goals",
        "expected",
    ),
    [
        (2, 1, "HOME"),
        (1, 1, "DRAW"),
        (0, 3, "AWAY"),
        (None, None, None),
        (1, None, None),
        (None, 1, None),
    ],
)
def test_get_match_result(
    home_goals,
    away_goals,
    expected,
):
    assert (
        get_match_result(
            home_goals,
            away_goals,
        )
        == expected
    )


@pytest.mark.parametrize(
    (
        "home_goals",
        "away_goals",
        "expected",
    ),
    [
        (2, 1, "played"),
        (0, 0, "played"),
        (None, None, "upcoming"),
        (1, None, "upcoming"),
        (None, 1, "upcoming"),
    ],
)
def test_get_match_status(
    home_goals,
    away_goals,
    expected,
):
    assert (
        get_match_status(
            home_goals,
            away_goals,
        )
        == expected
    )


# =============================================================================
# Parser
# =============================================================================


def test_parse_completed_historical_match():
    matches = parse_round_matches(
        season=2021,
        data=completed_match_payload(),
    )

    assert len(matches) == 1

    match = matches[0]

    assert match["season"] == 2021
    assert match["competition_id"] == 12487
    assert match["round"] == 1
    assert match["match_id"] == 817955
    assert match["match_number"] == 1

    assert match["home_team"] == "Cuiabá"
    assert match["home_goals"] == 2

    assert match["away_team"] == "Juventude"
    assert match["away_goals"] == 2

    assert match["date"] == "2021-05-29"
    assert match["time"] == "19:00"

    assert match["venue"] == "Arena Pantanal"
    assert match["city"] == "Cuiaba"
    assert match["state"] == "MT"

    assert match["status"] == "played"
    assert match["result"] == "DRAW"


def test_parse_future_match():
    matches = parse_round_matches(
        season=2026,
        data=future_match_payload(),
    )

    assert len(matches) == 1

    match = matches[0]

    assert match["season"] == 2026
    assert match["competition_id"] == 1260611

    assert match["home_goals"] is None
    assert match["away_goals"] is None

    assert match["date"] is None
    assert match["time"] is None

    assert match["status"] == "upcoming"
    assert match["result"] is None


def test_parse_location():
    venue, city, state = parse_location(
        "Maracanã - Rio de Janeiro - RJ"
    )

    assert venue == "Maracanã"
    assert city == "Rio de Janeiro"
    assert state == "RJ"


def test_parse_undefined_date():
    assert (
        parse_match_date(
            "A Definir"
        )
        is None
    )

    assert (
        parse_match_date(
            "A Confirmar"
        )
        is None
    )

    assert (
        parse_match_date(
            None
        )
        is None
    )


# =============================================================================
# DataFrame e validações
# =============================================================================


def test_build_history_dataframe_sorts_matches():
    first = parse_round_matches(
        season=2021,
        data=completed_match_payload(),
    )[0]

    second = {
        **first,
        "round": 2,
        "match_id": 817956,
        "match_number": 11,
    }

    dataframe = build_history_dataframe(
        [
            second,
            first,
        ]
    )

    assert dataframe[
        "match_id"
    ].tolist() == [
        817955,
        817956,
    ]


def test_history_dataframe_rejects_duplicate_match_ids():
    first = parse_round_matches(
        season=2021,
        data=completed_match_payload(),
    )[0]

    dataframe = pd.DataFrame(
        [
            first,
            first,
        ]
    )

    with pytest.raises(
        ValueError,
        match="duplicados",
    ):
        validate_history_dataframe(
            dataframe
        )


def test_season_validation_rejects_incomplete_season():
    match = parse_round_matches(
        season=2021,
        data=completed_match_payload(),
    )[0]

    with pytest.raises(
        ValueError,
        match="esperado 380 jogos",
    ):
        validate_season_matches(
            season=2021,
            matches=[match],
        )


# =============================================================================
# Snapshot real coletado
# =============================================================================


def test_history_snapshot_has_expected_shape():
    dataframe = load_history_dataframe()

    assert len(dataframe) == 2280

    assert set(
        dataframe[
            "season"
        ].unique()
    ) == {
        2021,
        2022,
        2023,
        2024,
        2025,
        2026,
    }

    counts = (
        dataframe
        .groupby("season")
        .size()
        .to_dict()
    )

    assert counts == {
        2021: 380,
        2022: 380,
        2023: 380,
        2024: 380,
        2025: 380,
        2026: 380,
    }


def test_history_snapshot_has_unique_match_ids():
    dataframe = load_history_dataframe()

    assert (
        dataframe[
            "match_id"
        ]
        .duplicated()
        .sum()
        == 0
    )


def test_completed_seasons_are_fully_played():
    dataframe = load_history_dataframe()

    completed_seasons = dataframe[
        dataframe[
            "season"
        ].between(
            2021,
            2025,
        )
    ]

    assert (
        completed_seasons[
            "status"
        ]
        == "played"
    ).all()

    assert (
        completed_seasons[
            "result"
        ]
        .notna()
        .all()
    )

    assert (
        completed_seasons[
            "home_goals"
        ]
        .notna()
        .all()
    )

    assert (
        completed_seasons[
            "away_goals"
        ]
        .notna()
        .all()
    )


def test_played_matches_have_complete_core_fields():
    dataframe = load_history_dataframe()

    played = dataframe[
        dataframe[
            "status"
        ] == "played"
    ]

    required_columns = [
        "season",
        "round",
        "match_id",
        "date",
        "time",
        "home_team_id",
        "home_team",
        "home_goals",
        "away_team_id",
        "away_team",
        "away_goals",
        "result",
    ]

    assert (
        played[
            required_columns
        ]
        .notna()
        .all()
        .all()
    )


def test_future_matches_do_not_have_result():
    dataframe = load_history_dataframe()

    upcoming = dataframe[
        dataframe[
            "status"
        ] == "upcoming"
    ]

    assert not upcoming.empty

    assert (
        upcoming[
            "result"
        ]
        .isna()
        .all()
    )

    assert (
        upcoming[
            "home_goals"
        ]
        .isna()
        .all()
    )

    assert (
        upcoming[
            "away_goals"
        ]
        .isna()
        .all()
    )