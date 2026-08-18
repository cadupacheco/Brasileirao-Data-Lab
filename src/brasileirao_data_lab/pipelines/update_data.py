from __future__ import annotations

import pandas as pd
import pytest

import brasileirao_data_lab.pipelines.update_data as update_data_module

from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.analytics.championship import (
    load_matches,
)
from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
    engine,
)
from brasileirao_data_lab.database.sync import (
    print_sync_result,
    sync_database,
)
from brasileirao_data_lab.database.validate import (
    validate_database_against_matches,
)
from brasileirao_data_lab.scrapers.cbf import (
    TOTAL_ROUNDS,
    create_session,
    fetch_all_matches,
    fetch_cbf_page,
    parse_standings,
    resolve_next_opponents,
    save_matches_csv,
    save_raw_html,
    save_standings_csv,
)


EXPECTED_TEAMS = 20
EXPECTED_MATCHES = 380


# =============================================================================
# Validação da classificação
# =============================================================================


def validate_standings(
    standings: list[dict[str, Any]],
) -> None:
    """Executa validações básicas da classificação."""

    if len(standings) != EXPECTED_TEAMS:

        raise ValueError(
            f"Esperados {EXPECTED_TEAMS} clubes, "
            f"mas foram encontrados "
            f"{len(standings)}."
        )

    positions = [
        team["position"]
        for team in standings
    ]

    if len(
        positions
    ) != len(
        set(
            positions
        )
    ):

        raise ValueError(
            "Existem posições duplicadas "
            "na classificação."
        )

    team_ids = [
        team["team_id"]
        for team in standings
    ]

    if len(
        team_ids
    ) != len(
        set(
            team_ids
        )
    ):

        raise ValueError(
            "Existem IDs de clubes duplicados."
        )


# =============================================================================
# Validação das partidas
# =============================================================================


def validate_matches(
    matches: list[dict[str, Any]],
) -> None:
    """Executa validações básicas dos jogos."""

    if not matches:

        raise ValueError(
            "Nenhuma partida foi encontrada."
        )

    match_ids = [
        match["match_id"]
        for match in matches
    ]

    if len(
        match_ids
    ) != len(
        set(
            match_ids
        )
    ):

        raise ValueError(
            "Existem partidas duplicadas."
        )

    invalid_rounds = [
        match["round"]
        for match in matches
        if not (
            1
            <= match["round"]
            <= TOTAL_ROUNDS
        )
    ]

    if invalid_rounds:

        raise ValueError(
            "Existem partidas com rodada inválida."
        )

    if len(
        matches
    ) != EXPECTED_MATCHES:

        print(
            f"[WARNING] Esperados "
            f"{EXPECTED_MATCHES} jogos, "
            f"mas foram encontrados "
            f"{len(matches)}."
        )


# =============================================================================
# Validação do Database
# =============================================================================


def raise_for_database_validation(
    validation_result: dict[str, Any],
) -> None:
    """
    Interrompe o pipeline se o banco divergir
    dos dados processados.
    """

    if validation_result[
        "exact_match"
    ]:

        return

    missing_count = len(
        validation_result.get(
            "missing_in_database",
            [],
        )
    )

    extra_count = len(
        validation_result.get(
            "extra_in_database",
            [],
        )
    )

    difference_count = int(
        validation_result.get(
            "difference_count",
            0,
        )
    )

    raise ValueError(
        "Validação CSV x Database falhou. "
        f"Ausentes no banco: {missing_count}. "
        f"Extras no banco: {extra_count}. "
        f"Divergências de campos: "
        f"{difference_count}."
    )


# =============================================================================
# Sincronização do Database
# =============================================================================


def sync_and_validate_database(
    matches: pd.DataFrame,
    database_engine: Engine | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    """
    Sincroniza os dados no banco e confirma
    que o conteúdo persistido continua idêntico
    ao DataFrame de origem.

    Toda a operação ocorre na mesma transação.

    Se a validação falhar:

        rollback

    Se a validação passar:

        commit
    """

    selected_engine = (
        database_engine
        or engine
    )

    selected_session_factory = (
        session_factory
        or SessionLocal
    )

    init_database(
        selected_engine
    )

    with selected_session_factory() as database_session:

        try:

            sync_result = sync_database(
                database_session,
                matches,
            )

            validation_result = (
                validate_database_against_matches(
                    database_session,
                    matches,
                )
            )

            raise_for_database_validation(
                validation_result
            )

            database_session.commit()

        except Exception:

            database_session.rollback()

            raise

    return (
        sync_result,
        validation_result,
    )


# =============================================================================
# Pipeline principal
# =============================================================================


def update_data() -> None:
    """Atualiza todos os dados principais do Brasileirão."""

    print()
    print("⚽ Brasileirão Data Lab")
    print("=" * 60)

    # =========================================================================
    # Página principal da CBF
    # =========================================================================

    session = create_session()

    try:

        print()
        print(
            "[INFO] Acessando a CBF..."
        )

        html = fetch_cbf_page(
            session=session
        )

    finally:

        session.close()

    print(
        f"[SUCCESS] Página coletada: "
        f"{len(html):,} caracteres"
    )

    raw_file = save_raw_html(
        html
    )

    print(
        f"[SUCCESS] HTML bruto salvo em: "
        f"{raw_file}"
    )

    # =========================================================================
    # Classificação
    # =========================================================================

    print()
    print(
        "[INFO] Extraindo classificação..."
    )

    standings = parse_standings(
        html
    )

    standings = resolve_next_opponents(
        standings
    )

    validate_standings(
        standings
    )

    standings_file = (
        save_standings_csv(
            standings
        )
    )

    print(
        f"[SUCCESS] "
        f"{len(standings)} clubes encontrados."
    )

    print(
        f"[SUCCESS] Classificação salva em: "
        f"{standings_file}"
    )

    print()
    print("Top 5:")
    print("-" * 60)

    for team in standings[
        :5
    ]:

        print(
            f"{team['position']:>2}º "
            f"{team['team']:<25} "
            f"{team['points']:>3} pts"
        )

    # =========================================================================
    # Jogos
    # =========================================================================

    print()
    print(
        "[INFO] Iniciando coleta "
        "das partidas..."
    )

    print()

    matches = fetch_all_matches()

    validate_matches(
        matches
    )

    matches_file = save_matches_csv(
        matches
    )

    played_matches = sum(
        1
        for match in matches
        if (
            match[
                "home_goals"
            ]
            is not None
            and match[
                "away_goals"
            ]
            is not None
        )
    )

    future_matches = (
        len(
            matches
        )
        - played_matches
    )

    print()
    print(
        f"[SUCCESS] "
        f"{len(matches)} partidas encontradas."
    )

    print(
        f"[INFO] Partidas com placar: "
        f"{played_matches}"
    )

    print(
        f"[INFO] Partidas sem placar: "
        f"{future_matches}"
    )

    print(
        f"[SUCCESS] Partidas salvas em: "
        f"{matches_file}"
    )

    # =========================================================================
    # Database
    # =========================================================================

    print()
    print("=" * 60)
    print("🗄️ DATABASE")
    print("=" * 60)

    print()
    print(
        "[INFO] Relendo matches.csv..."
    )

    matches_dataframe = load_matches()

    print(
        f"[SUCCESS] "
        f"{len(matches_dataframe)} partidas "
        f"carregadas do CSV."
    )

    print()
    print(
        "[INFO] Inicializando e "
        "sincronizando SQLite..."
    )

    (
        database_sync,
        database_validation,
    ) = sync_and_validate_database(
        matches_dataframe
    )

    # -------------------------------------------------------------------------
    # Resultado do sync
    # -------------------------------------------------------------------------

    print()
    print("SINCRONIZAÇÃO")
    print("-" * 60)

    print_sync_result(
        "Times",
        database_sync[
            "teams"
        ],
    )

    print_sync_result(
        "Partidas",
        database_sync[
            "matches"
        ],
    )

    print_sync_result(
        "Snapshots",
        database_sync[
            "standings_snapshots"
        ],
    )

    # -------------------------------------------------------------------------
    # Totais
    # -------------------------------------------------------------------------

    counts = database_sync[
        "counts"
    ]

    print()
    print("REGISTROS NO BANCO")
    print("-" * 60)

    print(
        f"Times: "
        f"{counts['teams']}"
    )

    print(
        f"Partidas: "
        f"{counts['matches']}"
    )

    print(
        f"Snapshots: "
        f"{counts['standings_snapshots']}"
    )

    # -------------------------------------------------------------------------
    # Validação
    # -------------------------------------------------------------------------

    print()
    print("VALIDAÇÃO CSV x DATABASE")
    print("-" * 60)

    print(
        f"CSV: "
        f"{database_validation['csv_count']} partidas"
    )

    print(
        f"Database: "
        f"{database_validation['database_count']} partidas"
    )

    print(
        f"IDs em comum: "
        f"{database_validation['common_count']}"
    )

    print(
        f"Ausentes no banco: "
        f"{len(database_validation['missing_in_database'])}"
    )

    print(
        f"Extras no banco: "
        f"{len(database_validation['extra_in_database'])}"
    )

    print(
        f"Divergências: "
        f"{database_validation['difference_count']}"
    )

    print()
    print(
        "✅ CSV e Database conferem."
    )

    # =========================================================================
    # Finalização
    # =========================================================================

    print()
    print("=" * 60)

    print(
        "[SUCCESS] Atualização concluída."
    )

    print(
        "[SUCCESS] CSV e SQLite sincronizados."
    )

    print("=" * 60)
    print()


if __name__ == "__main__":
    update_data()