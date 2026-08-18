from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from brasileirao_data_lab.analytics.championship import (
    get_championship_summary,
    get_home_away_stats,
    get_recent_form_table,
    get_team_stats,
)
from brasileirao_data_lab.analytics.evolution import (
    get_position_history,
)
from brasileirao_data_lab.database.models import (
    Match,
)
from brasileirao_data_lab.database.validate import (
    load_matches_from_database,
    normalize_matches_dataframe,
)


# =============================================================================
# Temporada
# =============================================================================


def get_latest_analytics_season(
    session: Session,
) -> int:
    """
    Retorna a temporada mais recente
    disponível no banco.
    """

    statement = select(
        func.max(
            Match.season
        )
    )

    season = session.scalar(
        statement
    )

    if season is None:

        raise ValueError(
            "O banco não possui partidas."
        )

    return int(
        season
    )


# =============================================================================
# DataFrame
# =============================================================================


def load_matches_for_analytics(
    session: Session,
    season: int | None = None,
) -> pd.DataFrame:
    """
    Carrega partidas do SQLite em formato
    compatível com os módulos de Analytics.

    O objetivo é entregar aos módulos existentes
    a mesma estrutura lógica utilizada pelo CSV.
    """

    selected_season = (
        season
        if season is not None
        else get_latest_analytics_season(
            session
        )
    )

    matches = load_matches_from_database(
        session,
        season=selected_season,
    )

    if matches.empty:

        raise ValueError(
            f"Nenhuma partida encontrada "
            f"para a temporada "
            f"{selected_season}."
        )

    return normalize_matches_dataframe(
        matches
    )


# =============================================================================
# Normalização de resultados
# =============================================================================


def normalize_result_value(
    value: Any,
) -> Any:
    """
    Normaliza valores usados na comparação
    dos resultados analíticos.
    """

    if value is None:
        return None

    if isinstance(
        value,
        float,
    ):

        return round(
            value,
            6,
        )

    return value


def normalize_records(
    dataframe: pd.DataFrame,
    sort_columns: list[str],
) -> list[dict[str, Any]]:
    """
    Converte um DataFrame analítico para
    registros determinísticos.
    """

    if dataframe.empty:
        return []

    existing_sort_columns = [
        column
        for column in sort_columns
        if column in dataframe.columns
    ]

    normalized = dataframe.copy()

    if existing_sort_columns:

        normalized = normalized.sort_values(
            by=existing_sort_columns
        )

    normalized = normalized.reset_index(
        drop=True
    )

    records = []

    for record in normalized.to_dict(
        orient="records"
    ):

        records.append(
            {
                key: normalize_result_value(
                    value
                )
                for key, value in record.items()
            }
        )

    return records


# =============================================================================
# Snapshot analítico
# =============================================================================


def build_analytics_snapshot(
    matches: pd.DataFrame,
) -> dict[str, Any]:
    """
    Executa um conjunto representativo
    dos Analytics da V0.2.

    Esse snapshot será utilizado para provar
    que CSV e SQLite produzem os mesmos resultados.
    """

    summary = get_championship_summary(
        matches
    )

    standings = get_team_stats(
        matches
    )

    home_away = get_home_away_stats(
        matches
    )

    recent_form = get_recent_form_table(
        matches,
        last_n=5,
    )

    position_history = get_position_history(
        matches
    )

    return {
        "summary": {
            key: normalize_result_value(
                value
            )
            for key, value in summary.items()
        },
        "standings": normalize_records(
            standings,
            sort_columns=[
                "team_id",
            ],
        ),
        "home_away": normalize_records(
            home_away,
            sort_columns=[
                "team_id",
            ],
        ),
        "recent_form": normalize_records(
            recent_form,
            sort_columns=[
                "team_id",
            ],
        ),
        "position_history": normalize_records(
            position_history,
            sort_columns=[
                "round",
                "team_id",
            ],
        ),
    }


# =============================================================================
# Comparação CSV x SQLite para Analytics
# =============================================================================


def compare_analytics_sources(
    csv_matches: pd.DataFrame,
    database_matches: pd.DataFrame,
) -> dict[str, Any]:
    """
    Compara os resultados dos Analytics
    utilizando duas fontes de partidas.

    Não compara apenas os registros crus.
    Compara os resultados produzidos pelos
    módulos analíticos.
    """

    csv_snapshot = build_analytics_snapshot(
        csv_matches
    )

    database_snapshot = (
        build_analytics_snapshot(
            database_matches
        )
    )

    sections = [
        "summary",
        "standings",
        "home_away",
        "recent_form",
        "position_history",
    ]

    section_results = {}

    for section in sections:

        section_results[
            section
        ] = (
            csv_snapshot[
                section
            ]
            == database_snapshot[
                section
            ]
        )

    exact_match = all(
        section_results.values()
    )

    return {
        "exact_match": exact_match,
        "sections": section_results,
        "csv_snapshot": csv_snapshot,
        "database_snapshot": (
            database_snapshot
        ),
    }