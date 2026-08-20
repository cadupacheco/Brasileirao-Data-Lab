from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from brasileirao_data_lab.pipelines.automated_project_update import (
    build_database_file,
    build_processed_matches_dataframe,
    build_project_artifacts,
    save_dataframe,
)
from brasileirao_data_lab.pipelines.update_detector import (
    CURRENT_SEASON,
    compare_match_snapshots,
    load_saved_history,
    print_update_check,
)


SIMULATED_HOME_GOALS = 2
SIMULATED_AWAY_GOALS = 1


# =============================================================================
# Temporada atual
# =============================================================================


def get_current_season(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Retorna somente os jogos da temporada atual.
    """

    current_season = (
        history[
            history[
                "season"
            ] == CURRENT_SEASON
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    if current_season.empty:
        raise ValueError(
            f"Nenhum jogo da temporada "
            f"{CURRENT_SEASON} foi encontrado."
        )

    return current_season


# =============================================================================
# Escolha segura de uma partida futura
# =============================================================================


def select_future_match(
    current_season: pd.DataFrame,
) -> pd.Series:
    """
    Seleciona a primeira partida futura realmente agendada.

    Não utiliza jogos upcoming que ainda estejam sem
    data ou horário definidos.

    Isso evita transformar artificialmente uma partida
    adiada/indefinida em played sem os dados essenciais
    exigidos pelo feature engineering.
    """

    future_matches = (
        current_season[
            current_season[
                "status"
            ] == "upcoming"
        ]
        .copy()
    )

    if future_matches.empty:
        raise ValueError(
            "Nenhuma partida futura disponível "
            "para realizar o dry-run."
        )

    # -------------------------------------------------------------------------
    # Cria datetime somente para partidas realmente agendadas
    # -------------------------------------------------------------------------

    future_matches[
        "scheduled_datetime"
    ] = pd.to_datetime(
        future_matches[
            "date"
        ].astype(
            "string"
        )
        + " "
        + future_matches[
            "time"
        ].astype(
            "string"
        ),
        errors="coerce",
    )

    scheduled_matches = (
        future_matches[
            future_matches[
                "scheduled_datetime"
            ].notna()
        ]
        .copy()
        .sort_values(
            by=[
                "scheduled_datetime",
                "round",
                "match_id",
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    if scheduled_matches.empty:
        raise ValueError(
            "Existem partidas futuras, mas nenhuma "
            "possui data e horário definidos."
        )

    return scheduled_matches.iloc[
        0
    ]


# =============================================================================
# Simulação de resultado
# =============================================================================


def simulate_finished_match(
    current_season: pd.DataFrame,
    match_id: int,
    home_goals: int = SIMULATED_HOME_GOALS,
    away_goals: int = SIMULATED_AWAY_GOALS,
) -> pd.DataFrame:
    """
    Cria uma cópia da temporada atual e transforma
    uma partida upcoming em played.

    Nenhum arquivo oficial é alterado.
    """

    simulated = (
        current_season
        .copy()
        .reset_index(
            drop=True
        )
    )

    mask = (
        simulated[
            "match_id"
        ] == match_id
    )

    if int(
        mask.sum()
    ) != 1:
        raise ValueError(
            f"Esperada exatamente uma partida "
            f"com match_id={match_id}."
        )

    match = (
        simulated.loc[
            mask
        ]
        .iloc[
            0
        ]
    )

    if (
        str(
            match[
                "status"
            ]
        )
        != "upcoming"
    ):
        raise ValueError(
            "A partida escolhida para simulação "
            "não está como upcoming."
        )

    # -------------------------------------------------------------------------
    # Proteção contra jogo sem data/hora
    # -------------------------------------------------------------------------

    if pd.isna(
        match[
            "date"
        ]
    ):
        raise ValueError(
            "A partida escolhida não possui data."
        )

    if pd.isna(
        match[
            "time"
        ]
    ):
        raise ValueError(
            "A partida escolhida não possui horário."
        )

    # -------------------------------------------------------------------------
    # Placar
    # -------------------------------------------------------------------------

    simulated.loc[
        mask,
        "home_goals",
    ] = home_goals

    simulated.loc[
        mask,
        "away_goals",
    ] = away_goals

    simulated.loc[
        mask,
        "status",
    ] = "played"

    # -------------------------------------------------------------------------
    # Resultado
    # -------------------------------------------------------------------------

    if home_goals > away_goals:
        result = "HOME"

    elif away_goals > home_goals:
        result = "AWAY"

    else:
        result = "DRAW"

    simulated.loc[
        mask,
        "result",
    ] = result

    return simulated


# =============================================================================
# Validação do dry-run
# =============================================================================


def validate_dry_run(
    previous_history: pd.DataFrame,
    simulated_history: pd.DataFrame,
    features: pd.DataFrame,
    predictions: pd.DataFrame,
    simulation: pd.DataFrame,
) -> None:
    """
    Confirma que exatamente um jogo saiu
    de upcoming e passou para played.
    """

    previous_played = int(
        (
            previous_history[
                "status"
            ] == "played"
        ).sum()
    )

    new_played = int(
        (
            simulated_history[
                "status"
            ] == "played"
        ).sum()
    )

    previous_future = int(
        (
            previous_history[
                "status"
            ] == "upcoming"
        ).sum()
    )

    new_future = int(
        (
            simulated_history[
                "status"
            ] == "upcoming"
        ).sum()
    )

    # -------------------------------------------------------------------------
    # Played + 1
    # -------------------------------------------------------------------------

    if new_played != (
        previous_played
        + 1
    ):
        raise ValueError(
            "O número de partidas disputadas "
            "não aumentou exatamente em 1."
        )

    # -------------------------------------------------------------------------
    # Upcoming - 1
    # -------------------------------------------------------------------------

    if new_future != (
        previous_future
        - 1
    ):
        raise ValueError(
            "O número de partidas futuras "
            "não diminuiu exatamente em 1."
        )

    # -------------------------------------------------------------------------
    # Features
    # -------------------------------------------------------------------------

    if len(
        features
    ) != new_played:
        raise ValueError(
            "Quantidade de features não corresponde "
            "às partidas disputadas."
        )

    # -------------------------------------------------------------------------
    # Previsões
    # -------------------------------------------------------------------------

    if len(
        predictions
    ) != new_future:
        raise ValueError(
            "Quantidade de previsões não corresponde "
            "às partidas futuras."
        )

    # -------------------------------------------------------------------------
    # Monte Carlo
    # -------------------------------------------------------------------------

    if len(
        simulation
    ) != 20:
        raise ValueError(
            "Monte Carlo não retornou os 20 clubes."
        )


# =============================================================================
# Main
# =============================================================================


def main() -> None:
    """
    Executa um teste completo da V0.7 sem modificar
    os dados oficiais do projeto.
    """

    print()
    print("⚽ Brasileirão Data Lab")
    print("🧪 Dry-run V0.7")
    print("=" * 72)

    # =========================================================================
    # Histórico oficial
    # =========================================================================

    print()
    print(
        "[INFO] Carregando histórico oficial..."
    )

    previous_history = (
        load_saved_history()
    )

    current_season = (
        get_current_season(
            previous_history
        )
    )

    played_before = int(
        (
            current_season[
                "status"
            ] == "played"
        ).sum()
    )

    future_before = int(
        (
            current_season[
                "status"
            ] == "upcoming"
        ).sum()
    )

    print(
        f"[INFO] 2026 antes da simulação: "
        f"{played_before} jogados | "
        f"{future_before} futuros"
    )

    # =========================================================================
    # Escolha do jogo
    # =========================================================================

    match = (
        select_future_match(
            current_season
        )
    )

    match_id = int(
        match[
            "match_id"
        ]
    )

    print()
    print(
        "[SIMULATION] Partida escolhida:"
    )

    print(
        f"Rodada "
        f"{int(match['round'])}"
    )

    print(
        f"{match['home_team']} "
        f"x "
        f"{match['away_team']}"
    )

    print(
        f"Data: "
        f"{match['date']}"
    )

    print(
        f"Horário: "
        f"{match['time']}"
    )

    print(
        f"match_id="
        f"{match_id}"
    )

    print(
        f"Placar artificial: "
        f"{SIMULATED_HOME_GOALS} x "
        f"{SIMULATED_AWAY_GOALS}"
    )

    # =========================================================================
    # Resultado artificial
    # =========================================================================

    simulated_current_season = (
        simulate_finished_match(
            current_season=current_season,
            match_id=match_id,
        )
    )

    # =========================================================================
    # Detector
    # =========================================================================

    check = (
        compare_match_snapshots(
            previous=current_season,
            current=simulated_current_season,
            season=CURRENT_SEASON,
        )
    )

    print_update_check(
        check
    )

    if not check.has_changes:
        raise ValueError(
            "O detector não percebeu "
            "a alteração simulada."
        )

    if (
        match_id
        not in check.newly_played_match_ids
    ):
        raise ValueError(
            "O detector não identificou "
            "a partida como newly played."
        )

    # =========================================================================
    # Reconstrução completa
    # =========================================================================

    print()
    print(
        "[INFO] Reconstruindo projeto "
        "com o resultado artificial..."
    )

    artifacts = (
        build_project_artifacts(
            previous_history=previous_history,
            current_season=simulated_current_season,
            season=CURRENT_SEASON,
        )
    )

    # =========================================================================
    # Validação
    # =========================================================================

    validate_dry_run(
        previous_history=previous_history,
        simulated_history=artifacts.ml.history,
        features=artifacts.ml.features,
        predictions=artifacts.ml.predictions,
        simulation=artifacts.ml.simulation,
    )

    updated_current_season = (
        artifacts
        .ml
        .history[
            artifacts
            .ml
            .history[
                "season"
            ] == CURRENT_SEASON
        ]
    )

    played_after = int(
        (
            updated_current_season[
                "status"
            ] == "played"
        ).sum()
    )

    future_after = int(
        (
            updated_current_season[
                "status"
            ] == "upcoming"
        ).sum()
    )

    # =========================================================================
    # Banco temporário
    # =========================================================================

    print()
    print("=" * 72)
    print("🗄️ BANCO TEMPORÁRIO")
    print("=" * 72)

    processed_matches = (
        build_processed_matches_dataframe(
            current_season=simulated_current_season,
            season=CURRENT_SEASON,
        )
    )

    with TemporaryDirectory(
        prefix="brasileirao-v07-dry-run-",
    ) as temporary_directory:

        temporary_path = Path(
            temporary_directory
        )

        matches_file = (
            temporary_path
            / "matches.csv"
        )

        database_file = (
            temporary_path
            / "brasileirao.db"
        )

        features_file = (
            temporary_path
            / "features.csv"
        )

        predictions_file = (
            temporary_path
            / "future_predictions.csv"
        )

        simulation_file = (
            temporary_path
            / "season_simulation.csv"
        )

        # ---------------------------------------------------------------------
        # CSV principal
        # ---------------------------------------------------------------------

        save_dataframe(
            processed_matches,
            matches_file,
        )

        # ---------------------------------------------------------------------
        # Features
        # ---------------------------------------------------------------------

        save_dataframe(
            artifacts.ml.features,
            features_file,
        )

        # ---------------------------------------------------------------------
        # Previsões
        # ---------------------------------------------------------------------

        save_dataframe(
            artifacts.ml.predictions,
            predictions_file,
        )

        # ---------------------------------------------------------------------
        # Monte Carlo
        # ---------------------------------------------------------------------

        save_dataframe(
            artifacts.ml.simulation,
            simulation_file,
        )

        # ---------------------------------------------------------------------
        # SQLite
        # ---------------------------------------------------------------------

        build_database_file(
            matches=processed_matches,
            database_file=database_file,
        )

        required_files = [
            matches_file,
            database_file,
            features_file,
            predictions_file,
            simulation_file,
        ]

        missing_files = [
            path
            for path in required_files
            if not path.exists()
        ]

        if missing_files:
            raise FileNotFoundError(
                "Arquivos temporários não foram "
                "criados corretamente."
            )

        print()
        print(
            "[SUCCESS] Todos os artefatos "
            "temporários foram criados."
        )

        print(
            "[INFO] Nenhum arquivo oficial "
            "foi modificado."
        )

    # =========================================================================
    # Resultado final
    # =========================================================================

    print()
    print("=" * 72)
    print("🏁 RESULTADO DO DRY-RUN")
    print("=" * 72)

    print(
        f"Jogados antes: "
        f"{played_before}"
    )

    print(
        f"Jogados depois: "
        f"{played_after}"
    )

    print(
        f"Futuros antes: "
        f"{future_before}"
    )

    print(
        f"Futuros depois: "
        f"{future_after}"
    )

    print(
        f"Features: "
        f"{len(artifacts.ml.features)}"
    )

    print(
        f"Previsões restantes: "
        f"{len(artifacts.ml.predictions)}"
    )

    print(
        f"Clubes no Monte Carlo: "
        f"{len(artifacts.ml.simulation)}"
    )

    print()
    print(
        "✅ DRY-RUN V0.7 CONCLUÍDO COM SUCESSO."
    )

    print(
        "✅ O resultado artificial foi processado."
    )

    print(
        "✅ Random Forest foi recalculado."
    )

    print(
        "✅ Monte Carlo foi recalculado."
    )

    print(
        "✅ SQLite temporário foi validado."
    )

    print(
        "✅ Dados oficiais permaneceram intactos."
    )

    print("=" * 72)
    print()


if __name__ == "__main__":
    main()