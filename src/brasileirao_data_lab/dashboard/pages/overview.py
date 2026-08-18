from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from brasileirao_data_lab.analytics.championship import (
    get_away_ranking,
    get_championship_summary,
    get_home_ranking,
    get_recent_form_table,
    get_team_stats,
)
from brasileirao_data_lab.analytics.evolution import (
    get_latest_played_round,
)
from brasileirao_data_lab.database.analytics_bridge import (
    load_matches_for_analytics,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
)


# =============================================================================
# Dados
# =============================================================================


@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def load_overview_data() -> dict[str, Any]:
    """
    Carrega os dados principais da Visão Geral.

    O SQLite é a fonte principal do Dashboard.
    Os cálculos reaproveitam os módulos de Analytics
    já existentes no projeto.
    """

    with SessionLocal() as session:

        matches = (
            load_matches_for_analytics(
                session
            )
        )

    summary = get_championship_summary(
        matches
    )

    standings = get_team_stats(
        matches
    )

    home_ranking = get_home_ranking(
        matches
    )

    away_ranking = get_away_ranking(
        matches
    )

    recent_form = get_recent_form_table(
        matches,
        last_n=5,
    )

    latest_round = get_latest_played_round(
        matches
    )

    season = int(
        matches[
            "season"
        ]
        .dropna()
        .max()
    )

    return {
        "matches": matches,
        "summary": summary,
        "standings": standings,
        "home_ranking": home_ranking,
        "away_ranking": away_ranking,
        "recent_form": recent_form,
        "latest_round": latest_round,
        "season": season,
    }


# =============================================================================
# Helpers
# =============================================================================


def get_best_attack(
    standings: pd.DataFrame,
) -> pd.Series | None:
    """Retorna o clube com mais gols marcados."""

    if standings.empty:
        return None

    index = standings[
        "goals_for"
    ].idxmax()

    return standings.loc[
        index
    ]


def get_best_defense(
    standings: pd.DataFrame,
) -> pd.Series | None:
    """Retorna o clube com menos gols sofridos."""

    if standings.empty:
        return None

    index = standings[
        "goals_against"
    ].idxmin()

    return standings.loc[
        index
    ]


def build_standings_table(
    standings: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepara a classificação para exibição
    no Dashboard.
    """

    if standings.empty:
        return pd.DataFrame()

    dataframe = standings[
        [
            "calculated_position",
            "team",
            "matches",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goals_against",
            "goal_difference",
            "points",
            "performance_pct",
        ]
    ].copy()

    dataframe = dataframe.rename(
        columns={
            "calculated_position": "Pos",
            "team": "Clube",
            "matches": "J",
            "wins": "V",
            "draws": "E",
            "losses": "D",
            "goals_for": "GP",
            "goals_against": "GC",
            "goal_difference": "SG",
            "points": "PTS",
            "performance_pct": "%",
        }
    )

    return dataframe


def build_recent_form_table(
    recent_form: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepara o ranking de momento
    para exibição.
    """

    if recent_form.empty:
        return pd.DataFrame()

    dataframe = recent_form[
        [
            "recent_position",
            "team",
            "recent_points",
            "recent_goals_for",
            "recent_goals_against",
            "recent_goal_difference",
            "recent_performance_pct",
            "recent_form",
        ]
    ].copy()

    dataframe = dataframe.rename(
        columns={
            "recent_position": "Pos",
            "team": "Clube",
            "recent_points": "PTS",
            "recent_goals_for": "GP",
            "recent_goals_against": "GC",
            "recent_goal_difference": "SG",
            "recent_performance_pct": "%",
            "recent_form": "Forma",
        }
    )

    return dataframe


def build_venue_table(
    ranking: pd.DataFrame,
    venue: str,
) -> pd.DataFrame:
    """
    Prepara ranking de mandantes
    ou visitantes para exibição.
    """

    if ranking.empty:
        return pd.DataFrame()

    if venue == "home":

        dataframe = ranking[
            [
                "home_position",
                "team",
                "home_matches",
                "home_wins",
                "home_draws",
                "home_losses",
                "home_points",
                "home_goal_difference",
                "home_performance_pct",
            ]
        ].copy()

        dataframe = dataframe.rename(
            columns={
                "home_position": "Pos",
                "team": "Clube",
                "home_matches": "J",
                "home_wins": "V",
                "home_draws": "E",
                "home_losses": "D",
                "home_points": "PTS",
                "home_goal_difference": "SG",
                "home_performance_pct": "%",
            }
        )

        return dataframe

    dataframe = ranking[
        [
            "away_position",
            "team",
            "away_matches",
            "away_wins",
            "away_draws",
            "away_losses",
            "away_points",
            "away_goal_difference",
            "away_performance_pct",
        ]
    ].copy()

    dataframe = dataframe.rename(
        columns={
            "away_position": "Pos",
            "team": "Clube",
            "away_matches": "J",
            "away_wins": "V",
            "away_draws": "E",
            "away_losses": "D",
            "away_points": "PTS",
            "away_goal_difference": "SG",
            "away_performance_pct": "%",
        }
    )

    return dataframe


# =============================================================================
# Carregamento
# =============================================================================


with st.spinner(
    "Carregando dados do campeonato..."
):

    data = load_overview_data()


summary = data[
    "summary"
]

standings = data[
    "standings"
]

home_ranking = data[
    "home_ranking"
]

away_ranking = data[
    "away_ranking"
]

recent_form = data[
    "recent_form"
]

season = data[
    "season"
]

latest_round = data[
    "latest_round"
]


# =============================================================================
# Cabeçalho
# =============================================================================


st.title(
    "🏠 Visão Geral"
)

st.caption(
    f"Campeonato Brasileiro Série A {season} "
    f"• Dados carregados do SQLite"
)


# =============================================================================
# Métricas principais
# =============================================================================


metric_1, metric_2, metric_3, metric_4 = (
    st.columns(
        4
    )
)


with metric_1:

    st.metric(
        label="Partidas realizadas",
        value=summary[
            "played_matches"
        ],
        delta=(
            f"{summary['future_matches']} restantes"
        ),
    )


with metric_2:

    st.metric(
        label="Gols marcados",
        value=summary[
            "total_goals"
        ],
        delta=(
            f"{summary['average_goals_per_match']:.2f} por jogo"
        ),
    )


with metric_3:

    leader = (
        standings.iloc[
            0
        ]
        if not standings.empty
        else None
    )

    if leader is not None:

        st.metric(
            label="Líder",
            value=leader[
                "team"
            ],
            delta=(
                f"{int(leader['points'])} pontos"
            ),
        )

    else:

        st.metric(
            label="Líder",
            value="-",
        )


with metric_4:

    st.metric(
        label="Última rodada computada",
        value=(
            f"{latest_round}ª"
            if latest_round
            else "-"
        ),
    )


# =============================================================================
# Destaques
# =============================================================================


best_attack = get_best_attack(
    standings
)

best_defense = get_best_defense(
    standings
)


st.subheader(
    "🔥 Destaques do campeonato"
)


highlight_1, highlight_2, highlight_3 = (
    st.columns(
        3
    )
)


with highlight_1:

    if best_attack is not None:

        st.metric(
            label="Melhor ataque",
            value=best_attack[
                "team"
            ],
            delta=(
                f"{int(best_attack['goals_for'])} gols"
            ),
        )


with highlight_2:

    if best_defense is not None:

        st.metric(
            label="Melhor defesa",
            value=best_defense[
                "team"
            ],
            delta=(
                f"{int(best_defense['goals_against'])} sofridos"
            ),
        )


with highlight_3:

    if not recent_form.empty:

        hottest_team = recent_form.iloc[
            0
        ]

        st.metric(
            label="Melhor momento",
            value=hottest_team[
                "team"
            ],
            delta=(
                f"{int(hottest_team['recent_points'])}/15 pontos"
            ),
        )


st.divider()


# =============================================================================
# Classificação
# =============================================================================


st.subheader(
    "🏆 Classificação"
)

standings_table = (
    build_standings_table(
        standings
    )
)

st.dataframe(
    standings_table,
    hide_index=True,
)


st.divider()


# =============================================================================
# Forma recente
# =============================================================================


st.subheader(
    "⚡ Momento dos clubes"
)

st.caption(
    "Desempenho nos últimos 5 jogos."
)

recent_table = (
    build_recent_form_table(
        recent_form
    )
)

st.dataframe(
    recent_table,
    hide_index=True,
)


st.divider()


# =============================================================================
# Casa x Fora
# =============================================================================


st.subheader(
    "🏟️ Desempenho por mando"
)


home_tab, away_tab = st.tabs(
    [
        "🏠 Mandantes",
        "✈️ Visitantes",
    ]
)


with home_tab:

    home_table = (
        build_venue_table(
            home_ranking,
            venue="home",
        )
    )

    st.dataframe(
        home_table,
        hide_index=True,
    )


with away_tab:

    away_table = (
        build_venue_table(
            away_ranking,
            venue="away",
        )
    )

    st.dataframe(
        away_table,
        hide_index=True,
    )


# =============================================================================
# Rodapé
# =============================================================================


st.divider()

st.caption(
    "Brasileirão Data Lab • "
    "V0.4 Dashboard • "
    "Fonte principal: SQLite"
)