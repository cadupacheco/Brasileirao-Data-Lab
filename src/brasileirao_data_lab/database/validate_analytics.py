from __future__ import annotations

from typing import Any

from brasileirao_data_lab.analytics.championship import (
    load_matches,
)
from brasileirao_data_lab.database.analytics_bridge import (
    compare_analytics_sources,
    load_matches_for_analytics,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
)


ANALYTICS_SECTIONS = [
    "summary",
    "standings",
    "home_away",
    "recent_form",
    "position_history",
]


# =============================================================================
# Validação
# =============================================================================


def raise_for_analytics_validation(
    result: dict[str, Any],
) -> None:
    """
    Interrompe a execução se CSV e SQLite
    produzirem resultados analíticos diferentes.
    """

    if result[
        "exact_match"
    ]:

        return

    failed_sections = [
        section
        for section, passed
        in result[
            "sections"
        ].items()
        if not passed
    ]

    failed_text = ", ".join(
        failed_sections
    )

    raise ValueError(
        "Analytics CSV x SQLite divergiram. "
        f"Seções: {failed_text}"
    )


def validate_real_analytics() -> dict[str, Any]:
    """
    Compara os Analytics gerados pelo matches.csv
    com os Analytics gerados pelas partidas
    armazenadas no SQLite.
    """

    csv_matches = load_matches()

    with SessionLocal() as session:

        database_matches = (
            load_matches_for_analytics(
                session
            )
        )

    result = compare_analytics_sources(
        csv_matches,
        database_matches,
    )

    raise_for_analytics_validation(
        result
    )

    return result


# =============================================================================
# Terminal
# =============================================================================


def print_validation_result(
    result: dict[str, Any],
) -> None:
    """Exibe o resultado da validação."""

    print()
    print("RESULTADOS")
    print("-" * 72)

    for section in ANALYTICS_SECTIONS:

        passed = result[
            "sections"
        ][
            section
        ]

        status = (
            "✅ IGUAL"
            if passed
            else "❌ DIFERENTE"
        )

        print(
            f"{section:<24} "
            f"{status}"
        )

    print()

    if result[
        "exact_match"
    ]:

        print(
            "✅ CSV e SQLite produzem "
            "os mesmos resultados analíticos."
        )

    else:

        print(
            "❌ Foram encontradas divergências "
            "nos Analytics."
        )


def main() -> None:
    """Executa validação analítica real."""

    print()
    print("⚽ Brasileirão Data Lab")
    print(
        "🔬 V0.3 - Analytics CSV x SQLite"
    )
    print("=" * 72)

    print()
    print(
        "[INFO] Carregando matches.csv..."
    )

    print(
        "[INFO] Carregando partidas do SQLite..."
    )

    print(
        "[INFO] Executando Analytics "
        "nas duas fontes..."
    )

    result = validate_real_analytics()

    print_validation_result(
        result
    )

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()