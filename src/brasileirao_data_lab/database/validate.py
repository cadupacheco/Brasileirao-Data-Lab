from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from brasileirao_data_lab.analytics.championship import (
    load_matches,
)
from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.database.models import (
    Match,
    Team,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
    engine,
)
from brasileirao_data_lab.database.sync import (
    infer_season,
    is_missing,
    optional_date,
    optional_time,
)


# =============================================================================
# Colunas
# =============================================================================


MATCH_COMPARISON_COLUMNS = [
    "season",
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
]


NUMERIC_COLUMNS = [
    "season",
    "round",
    "match_id",
    "match_number",
    "home_team_id",
    "home_goals",
    "away_team_id",
    "away_goals",
]


TEXT_COLUMNS = [
    "group",
    "home_team",
    "away_team",
    "venue",
    "city",
    "state",
    "championship",
]


# =============================================================================
# Leitura do banco
# =============================================================================


def load_matches_from_database(
    session: Session,
    season: int | None = None,
) -> pd.DataFrame:
    """
    Carrega as partidas armazenadas no banco.

    Os nomes de mandante e visitante são recuperados
    através da tabela teams.
    """

    home_team = aliased(
        Team
    )

    away_team = aliased(
        Team
    )

    statement = (
        select(
            Match.season.label(
                "season"
            ),
            Match.round.label(
                "round"
            ),
            Match.match_id.label(
                "match_id"
            ),
            Match.match_number.label(
                "match_number"
            ),
            Match.group.label(
                "group"
            ),
            Match.date.label(
                "date"
            ),
            Match.time.label(
                "time"
            ),
            Match.home_team_id.label(
                "home_team_id"
            ),
            home_team.name.label(
                "home_team"
            ),
            Match.home_goals.label(
                "home_goals"
            ),
            Match.away_team_id.label(
                "away_team_id"
            ),
            away_team.name.label(
                "away_team"
            ),
            Match.away_goals.label(
                "away_goals"
            ),
            Match.venue.label(
                "venue"
            ),
            Match.city.label(
                "city"
            ),
            Match.state.label(
                "state"
            ),
            Match.championship.label(
                "championship"
            ),
        )
        .join(
            home_team,
            Match.home_team_id
            == home_team.team_id,
        )
        .join(
            away_team,
            Match.away_team_id
            == away_team.team_id,
        )
    )

    if season is not None:

        statement = statement.where(
            Match.season
            == season
        )

    statement = statement.order_by(
        Match.round,
        Match.match_number,
        Match.match_id,
    )

    rows = session.execute(
        statement
    ).all()

    records = [
        dict(
            row._mapping
        )
        for row in rows
    ]

    return pd.DataFrame(
        records,
        columns=MATCH_COMPARISON_COLUMNS,
    )


# =============================================================================
# Normalização
# =============================================================================


def normalize_text(
    value: Any,
) -> str | None:
    """Normaliza textos opcionais."""

    if is_missing(
        value
    ):
        return None

    text = str(
        value
    ).strip()

    if not text:
        return None

    return text


def normalize_date(
    value: Any,
) -> str | None:
    """Normaliza datas para YYYY-MM-DD."""

    parsed = optional_date(
        value
    )

    if parsed is None:
        return None

    return parsed.isoformat()


def normalize_time(
    value: Any,
) -> str | None:
    """Normaliza horários para HH:MM."""

    parsed = optional_time(
        value
    )

    if parsed is None:
        return None

    return parsed.strftime(
        "%H:%M"
    )


def force_none_for_missing(
    series: pd.Series,
) -> pd.Series:
    """
    Garante que valores ausentes sejam representados
    por None em vez de NaN.

    O Pandas pode converter automaticamente None para
    NaN durante operações como map(). Para nossa
    representação canônica queremos None.
    """

    series = series.astype(
        object
    )

    return series.where(
        series.notna(),
        None,
    )


def validate_required_columns(
    dataframe: pd.DataFrame,
) -> None:
    """Confirma que o DataFrame possui todas as colunas."""

    missing_columns = [
        column
        for column in MATCH_COMPARISON_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:

        raise ValueError(
            "Colunas obrigatórias ausentes: "
            + ", ".join(
                missing_columns
            )
        )


def normalize_matches_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Converte um dataset de partidas para uma
    representação canônica.

    Isso elimina diferenças puramente de tipo entre:

    CSV:
        "2026-08-23"
        "19:30"
        NaN

    SQLite:
        datetime.date(...)
        datetime.time(...)
        None

    Representação canônica:

        datas      -> YYYY-MM-DD ou None
        horários   -> HH:MM ou None
        textos     -> str ou None
        números    -> Int64
    """

    validate_required_columns(
        dataframe
    )

    normalized = dataframe[
        MATCH_COMPARISON_COLUMNS
    ].copy()

    # -------------------------------------------------------------------------
    # Números
    # -------------------------------------------------------------------------

    for column in NUMERIC_COLUMNS:

        normalized[
            column
        ] = pd.to_numeric(
            normalized[
                column
            ],
            errors="coerce",
        ).astype(
            "Int64"
        )

    # -------------------------------------------------------------------------
    # Textos
    # -------------------------------------------------------------------------

    for column in TEXT_COLUMNS:

        normalized[
            column
        ] = normalized[
            column
        ].map(
            normalize_text
        )

        normalized[
            column
        ] = force_none_for_missing(
            normalized[
                column
            ]
        )

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    normalized[
        "date"
    ] = normalized[
        "date"
    ].map(
        normalize_date
    )

    normalized[
        "date"
    ] = force_none_for_missing(
        normalized[
            "date"
        ]
    )

    # -------------------------------------------------------------------------
    # Horário
    # -------------------------------------------------------------------------

    normalized[
        "time"
    ] = normalized[
        "time"
    ].map(
        normalize_time
    )

    normalized[
        "time"
    ] = force_none_for_missing(
        normalized[
            "time"
        ]
    )

    # -------------------------------------------------------------------------
    # Ordem
    # -------------------------------------------------------------------------

    normalized = (
        normalized.sort_values(
            by="match_id"
        )
        .reset_index(
            drop=True
        )
    )

    return normalized


# =============================================================================
# Comparação
# =============================================================================


def values_are_equal(
    value_a: Any,
    value_b: Any,
) -> bool:
    """
    Compara dois valores tratando
    ausências corretamente.
    """

    missing_a = is_missing(
        value_a
    )

    missing_b = is_missing(
        value_b
    )

    if (
        missing_a
        and missing_b
    ):
        return True

    if (
        missing_a
        != missing_b
    ):
        return False

    return bool(
        value_a
        == value_b
    )


def compare_matches_dataframes(
    csv_matches: pd.DataFrame,
    database_matches: pd.DataFrame,
) -> dict[str, Any]:
    """
    Compara as partidas do CSV com as partidas
    lidas do banco.

    A identidade utilizada é match_id.
    """

    csv_normalized = (
        normalize_matches_dataframe(
            csv_matches
        )
    )

    database_normalized = (
        normalize_matches_dataframe(
            database_matches
        )
    )

    csv_by_id = (
        csv_normalized.set_index(
            "match_id",
            drop=False,
        )
    )

    database_by_id = (
        database_normalized.set_index(
            "match_id",
            drop=False,
        )
    )

    csv_ids = {
        int(
            value
        )
        for value in csv_by_id.index
    }

    database_ids = {
        int(
            value
        )
        for value in database_by_id.index
    }

    missing_in_database = sorted(
        csv_ids
        - database_ids
    )

    extra_in_database = sorted(
        database_ids
        - csv_ids
    )

    common_ids = sorted(
        csv_ids
        & database_ids
    )

    differences = []

    comparison_columns = [
        column
        for column in MATCH_COMPARISON_COLUMNS
        if column != "match_id"
    ]

    for match_id in common_ids:

        csv_row = csv_by_id.loc[
            match_id
        ]

        database_row = (
            database_by_id.loc[
                match_id
            ]
        )

        for column in comparison_columns:

            csv_value = csv_row[
                column
            ]

            database_value = (
                database_row[
                    column
                ]
            )

            if not values_are_equal(
                csv_value,
                database_value,
            ):

                differences.append(
                    {
                        "match_id": match_id,
                        "column": column,
                        "csv_value": csv_value,
                        "database_value": (
                            database_value
                        ),
                    }
                )

    exact_match = (
        not missing_in_database
        and not extra_in_database
        and not differences
        and len(
            csv_normalized
        )
        == len(
            database_normalized
        )
    )

    return {
        "exact_match": (
            exact_match
        ),
        "csv_count": len(
            csv_normalized
        ),
        "database_count": len(
            database_normalized
        ),
        "common_count": len(
            common_ids
        ),
        "missing_in_database": (
            missing_in_database
        ),
        "extra_in_database": (
            extra_in_database
        ),
        "differences": (
            differences
        ),
        "difference_count": len(
            differences
        ),
    }


# =============================================================================
# Validação completa
# =============================================================================


def validate_database_against_matches(
    session: Session,
    csv_matches: pd.DataFrame,
) -> dict[str, Any]:
    """
    Carrega do banco a mesma temporada do DataFrame
    e executa a comparação completa.
    """

    season = infer_season(
        csv_matches
    )

    database_matches = (
        load_matches_from_database(
            session,
            season=season,
        )
    )

    comparison = (
        compare_matches_dataframes(
            csv_matches,
            database_matches,
        )
    )

    comparison[
        "season"
    ] = season

    return comparison


# =============================================================================
# Terminal
# =============================================================================


def main() -> None:
    """Valida SQLite contra matches.csv."""

    print()
    print("⚽ Brasileirão Data Lab")
    print("🔎 V0.3 - Validação CSV x Database")
    print("=" * 76)

    print()
    print(
        "[INFO] Carregando matches.csv..."
    )

    csv_matches = load_matches()

    season = infer_season(
        csv_matches
    )

    print(
        f"[INFO] Temporada: "
        f"{season}"
    )

    print(
        f"[INFO] Partidas no CSV: "
        f"{len(csv_matches)}"
    )

    init_database(
        engine
    )

    with SessionLocal() as session:

        result = (
            validate_database_against_matches(
                session,
                csv_matches,
            )
        )

    print()
    print("COMPARAÇÃO")
    print("-" * 76)

    print(
        f"CSV: "
        f"{result['csv_count']} partidas"
    )

    print(
        f"Database: "
        f"{result['database_count']} partidas"
    )

    print(
        f"IDs em comum: "
        f"{result['common_count']}"
    )

    print(
        f"Ausentes no banco: "
        f"{len(result['missing_in_database'])}"
    )

    print(
        f"Extras no banco: "
        f"{len(result['extra_in_database'])}"
    )

    print(
        f"Divergências de campos: "
        f"{result['difference_count']}"
    )

    # -------------------------------------------------------------------------
    # Ausentes
    # -------------------------------------------------------------------------

    if result[
        "missing_in_database"
    ]:

        print()
        print(
            "IDs ausentes no banco:"
        )

        print(
            result[
                "missing_in_database"
            ][:20]
        )

    # -------------------------------------------------------------------------
    # Extras
    # -------------------------------------------------------------------------

    if result[
        "extra_in_database"
    ]:

        print()
        print(
            "IDs extras no banco:"
        )

        print(
            result[
                "extra_in_database"
            ][:20]
        )

    # -------------------------------------------------------------------------
    # Divergências
    # -------------------------------------------------------------------------

    if result[
        "differences"
    ]:

        print()
        print(
            "Primeiras divergências:"
        )

        for difference in (
            result[
                "differences"
            ][:20]
        ):

            print(
                f"  match_id="
                f"{difference['match_id']} | "
                f"{difference['column']} | "
                f"CSV="
                f"{difference['csv_value']!r} | "
                f"DB="
                f"{difference['database_value']!r}"
            )

    print()

    if result[
        "exact_match"
    ]:

        print(
            "✅ CSV e Database são idênticos "
            "para todas as partidas."
        )

    else:

        print(
            "❌ CSV e Database possuem "
            "divergências."
        )

    print()
    print("=" * 76)


if __name__ == "__main__":
    main()