from __future__ import annotations

import os
import shutil

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from brasileirao_data_lab.ml.features import (
    build_feature_dataset,
    get_features_file,
    validate_feature_dataset,
)
from brasileirao_data_lab.ml.predictions import (
    generate_future_predictions,
    get_predictions_file,
    validate_predictions,
)
from brasileirao_data_lab.ml.simulation import (
    DEFAULT_RANDOM_SEED,
    DEFAULT_SIMULATIONS,
    get_simulation_file,
    simulate_season,
    validate_simulation_result,
)
from brasileirao_data_lab.pipelines.update_detector import (
    CURRENT_SEASON,
    UpdateCheckResult,
    compare_match_snapshots,
    fetch_current_season_dataframe,
    load_saved_history,
    print_update_check,
)
from brasileirao_data_lab.scrapers.cbf_history import (
    get_history_output_file,
    validate_history_dataframe,
)


EXPECTED_CURRENT_SEASON_MATCHES = 380
EXPECTED_TEAMS = 20


# =============================================================================
# Resultado do pipeline
# =============================================================================


@dataclass(frozen=True)
class MLArtifacts:
    """
    Conjunto completo de artefatos gerados pelo pipeline de Machine Learning.
    """

    history: pd.DataFrame
    features: pd.DataFrame
    predictions: pd.DataFrame
    simulation: pd.DataFrame


@dataclass(frozen=True)
class AutomatedMLUpdateResult:
    """
    Resultado da execução automática.

    updated=False:
        nenhuma mudança foi encontrada na CBF.

    updated=True:
        novos artefatos foram gerados e publicados.
    """

    updated: bool
    check: UpdateCheckResult
    played_matches: int
    future_matches: int


# =============================================================================
# Validação da temporada atual
# =============================================================================


def validate_current_season_snapshot(
    dataframe: pd.DataFrame,
    season: int = CURRENT_SEASON,
    expected_matches: int = EXPECTED_CURRENT_SEASON_MATCHES,
) -> None:
    """
    Confirma que o snapshot atual recebido da CBF é seguro.

    O objetivo é impedir que uma resposta incompleta da CBF
    substitua os dados válidos já existentes.
    """

    if dataframe.empty:
        raise ValueError(
            "Snapshot atual da CBF está vazio."
        )

    season_data = (
        dataframe[
            dataframe["season"] == season
        ]
        .copy()
    )

    if season_data.empty:
        raise ValueError(
            f"Nenhuma partida da temporada "
            f"{season} foi encontrada."
        )

    if len(
        season_data
    ) != expected_matches:
        raise ValueError(
            f"Temporada {season}: esperado "
            f"{expected_matches} jogos, "
            f"recebidos {len(season_data)}."
        )

    if season_data[
        "match_id"
    ].duplicated().any():
        raise ValueError(
            "Snapshot atual possui match_id duplicados."
        )

    if season_data[
        "home_team"
    ].isna().any():
        raise ValueError(
            "Existem partidas sem clube mandante."
        )

    if season_data[
        "away_team"
    ].isna().any():
        raise ValueError(
            "Existem partidas sem clube visitante."
        )

    valid_statuses = {
        "played",
        "upcoming",
    }

    statuses = set(
        season_data[
            "status"
        ]
        .dropna()
        .astype(str)
        .unique()
    )

    if not statuses.issubset(
        valid_statuses
    ):
        raise ValueError(
            "Foram encontrados status inválidos "
            f"no snapshot atual: {sorted(statuses)}"
        )


# =============================================================================
# Histórico atualizado
# =============================================================================


def build_updated_history(
    previous_history: pd.DataFrame,
    current_season: pd.DataFrame,
    season: int = CURRENT_SEASON,
    expected_matches: int = EXPECTED_CURRENT_SEASON_MATCHES,
) -> pd.DataFrame:
    """
    Substitui somente a temporada atual dentro do histórico.

    Temporadas antigas permanecem exatamente como estavam.

    Exemplo:

        2021
        2022
        2023
        2024
        2025
        2026 antigo

    vira:

        2021
        2022
        2023
        2024
        2025
        2026 coletado agora
    """

    validate_history_dataframe(
        previous_history
    )

    validate_current_season_snapshot(
        dataframe=current_season,
        season=season,
        expected_matches=expected_matches,
    )

    past_seasons = (
        previous_history[
            previous_history[
                "season"
            ] != season
        ]
        .copy()
    )

    new_current_season = (
        current_season[
            current_season[
                "season"
            ] == season
        ]
        .copy()
    )

    updated_history = pd.concat(
        [
            past_seasons,
            new_current_season,
        ],
        ignore_index=True,
    )

    updated_history = (
        updated_history
        .sort_values(
            by=[
                "season",
                "round",
                "match_number",
                "match_id",
            ],
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )

    validate_history_dataframe(
        updated_history
    )

    expected_total = (
        len(
            past_seasons
        )
        + expected_matches
    )

    if len(
        updated_history
    ) != expected_total:
        raise ValueError(
            "Quantidade final do histórico "
            "não corresponde ao esperado."
        )

    return updated_history


# =============================================================================
# Contadores
# =============================================================================


def count_played_matches(
    history: pd.DataFrame,
) -> int:
    """
    Retorna quantas partidas já foram disputadas.
    """

    return int(
        (
            history[
                "status"
            ] == "played"
        ).sum()
    )


def count_future_matches(
    history: pd.DataFrame,
) -> int:
    """
    Retorna quantas partidas ainda estão pendentes.
    """

    return int(
        (
            history[
                "status"
            ] == "upcoming"
        ).sum()
    )


# =============================================================================
# Construção dos artefatos
# =============================================================================


def build_ml_artifacts(
    history: pd.DataFrame,
) -> MLArtifacts:
    """
    Reconstrói todo o bloco de ML usando o histórico atualizado.

    Nenhum arquivo é salvo durante esta etapa.

    Tudo é construído primeiro em memória.
    """

    print()
    print("=" * 72)
    print("🧠 MACHINE LEARNING")
    print("=" * 72)

    played_matches = count_played_matches(
        history
    )

    future_matches = count_future_matches(
        history
    )

    print()
    print(
        f"[INFO] Partidas disputadas: "
        f"{played_matches}"
    )

    print(
        f"[INFO] Partidas futuras: "
        f"{future_matches}"
    )

    # =========================================================================
    # Features
    # =========================================================================

    print()
    print(
        "[INFO] Reconstruindo features..."
    )

    features = build_feature_dataset(
        history
    )

    validate_feature_dataset(
        features
    )

    if len(
        features
    ) != played_matches:
        raise ValueError(
            "Quantidade de linhas do dataset "
            "de features difere da quantidade "
            "de partidas disputadas."
        )

    print(
        f"[SUCCESS] "
        f"{len(features)} linhas de features."
    )

    # =========================================================================
    # Previsões
    # =========================================================================

    if future_matches <= 0:
        raise ValueError(
            "Não existem partidas futuras. "
            "O comportamento de fim de temporada "
            "será tratado separadamente."
        )

    print()
    print(
        "[INFO] Treinando Random Forest "
        "e gerando novas previsões..."
    )

    predictions = (
        generate_future_predictions(
            feature_dataset=features,
            history=history,
        )
    )

    validate_predictions(
        predictions
    )

    if len(
        predictions
    ) != future_matches:
        raise ValueError(
            "Quantidade de previsões geradas "
            "difere da quantidade de partidas futuras."
        )

    print(
        f"[SUCCESS] "
        f"{len(predictions)} previsões geradas."
    )

    # =========================================================================
    # Monte Carlo
    # =========================================================================

    print()
    print(
        "[INFO] Executando Monte Carlo..."
    )

    simulation = simulate_season(
        history=history,
        predictions=predictions,
        simulations=DEFAULT_SIMULATIONS,
        seed=DEFAULT_RANDOM_SEED,
    )

    validate_simulation_result(
        simulation
    )

    if len(
        simulation
    ) != EXPECTED_TEAMS:
        raise ValueError(
            "Resultado da simulação não possui "
            f"os {EXPECTED_TEAMS} clubes esperados."
        )

    print(
        f"[SUCCESS] Monte Carlo concluído "
        f"com {DEFAULT_SIMULATIONS:,} simulações."
        .replace(
            ",",
            ".",
        )
    )

    return MLArtifacts(
        history=history,
        features=features,
        predictions=predictions,
        simulation=simulation,
    )


# =============================================================================
# Caminhos
# =============================================================================


def get_artifact_targets(
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """
    Retorna os caminhos oficiais dos quatro artefatos.

    output_dir existe principalmente para facilitar testes.
    """

    if output_dir is not None:

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return {
            "history": (
                output_dir
                / "matches_history.csv"
            ),
            "features": (
                output_dir
                / "features.csv"
            ),
            "predictions": (
                output_dir
                / "future_predictions.csv"
            ),
            "simulation": (
                output_dir
                / "season_simulation.csv"
            ),
        }

    return {
        "history": (
            get_history_output_file()
        ),
        "features": (
            get_features_file()
        ),
        "predictions": (
            get_predictions_file()
        ),
        "simulation": (
            get_simulation_file()
        ),
    }


# =============================================================================
# Escrita segura
# =============================================================================


def save_dataframe(
    dataframe: pd.DataFrame,
    path: Path,
) -> None:
    """
    Salva um DataFrame no padrão utilizado pelo projeto.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
    )


def save_ml_artifacts_atomically(
    artifacts: MLArtifacts,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """
    Publica os quatro artefatos somente depois que TODOS
    foram gerados e validados.

    Estratégia:

    1. escreve tudo em arquivos temporários;
    2. cria backup dos arquivos atuais;
    3. substitui os arquivos oficiais;
    4. se qualquer substituição falhar, restaura os backups.
    """

    targets = get_artifact_targets(
        output_dir=output_dir
    )

    dataframes = {
        "history": artifacts.history,
        "features": artifacts.features,
        "predictions": artifacts.predictions,
        "simulation": artifacts.simulation,
    }

    base_directory = (
        next(
            iter(
                targets.values()
            )
        )
        .parent
    )

    base_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    with TemporaryDirectory(
        prefix=".v07-update-",
        dir=base_directory,
    ) as temporary_directory:

        temporary_path = Path(
            temporary_directory
        )

        staged_files: dict[
            str,
            Path,
        ] = {}

        backup_files: dict[
            str,
            Path,
        ] = {}

        # =====================================================================
        # Staging
        # =====================================================================

        for name, dataframe in (
            dataframes.items()
        ):

            staging_file = (
                temporary_path
                / f"{name}.new.csv"
            )

            save_dataframe(
                dataframe,
                staging_file,
            )

            staged_files[
                name
            ] = staging_file

        # =====================================================================
        # Backup
        # =====================================================================

        for name, target in (
            targets.items()
        ):

            if not target.exists():
                continue

            backup_file = (
                temporary_path
                / f"{name}.backup.csv"
            )

            shutil.copy2(
                target,
                backup_file,
            )

            backup_files[
                name
            ] = backup_file

        replaced_files: list[
            str
        ] = []

        try:

            # =================================================================
            # Publicação
            # =================================================================

            for name, target in (
                targets.items()
            ):

                os.replace(
                    staged_files[
                        name
                    ],
                    target,
                )

                replaced_files.append(
                    name
                )

        except Exception:

            # =================================================================
            # Rollback
            # =================================================================

            for name in reversed(
                replaced_files
            ):

                target = targets[
                    name
                ]

                backup = backup_files.get(
                    name
                )

                if (
                    backup is not None
                    and backup.exists()
                ):

                    shutil.copy2(
                        backup,
                        target,
                    )

                elif target.exists():

                    target.unlink()

            raise

    return targets


# =============================================================================
# Pipeline automático
# =============================================================================


def run_automated_ml_update(
    season: int = CURRENT_SEASON,
    delay: float = 0.20,
) -> AutomatedMLUpdateResult:
    """
    Executa a atualização automática do bloco de Machine Learning.

    Se a CBF estiver igual ao snapshot salvo:
        encerra imediatamente.

    Se houver alteração:
        reconstrói tudo e publica os novos artefatos.
    """

    print()
    print("⚽ Brasileirão Data Lab")
    print("🤖 Atualização automática V0.7")
    print("=" * 72)

    print()
    print(
        "[INFO] Carregando snapshot atual..."
    )

    previous_history = (
        load_saved_history()
    )

    print(
        f"[SUCCESS] "
        f"{len(previous_history)} partidas "
        "carregadas do histórico."
    )

    print()
    print(
        f"[INFO] Consultando temporada "
        f"{season} na CBF..."
    )

    current_season = (
        fetch_current_season_dataframe(
            season=season,
            delay=delay,
        )
    )

    check = compare_match_snapshots(
        previous=previous_history,
        current=current_season,
        season=season,
    )

    print_update_check(
        check
    )

    # =========================================================================
    # Nada mudou
    # =========================================================================

    if not check.has_changes:

        played_matches = (
            count_played_matches(
                previous_history
            )
        )

        future_matches = (
            count_future_matches(
                previous_history
            )
        )

        print(
            "[SUCCESS] Nenhuma atualização necessária."
        )

        print(
            "[INFO] Features, modelo e Monte Carlo "
            "não serão executados."
        )

        return AutomatedMLUpdateResult(
            updated=False,
            check=check,
            played_matches=played_matches,
            future_matches=future_matches,
        )

    # =========================================================================
    # Mudança encontrada
    # =========================================================================

    print()
    print(
        "[INFO] Alteração confirmada."
    )

    print(
        "[INFO] Preparando novo histórico..."
    )

    updated_history = (
        build_updated_history(
            previous_history=previous_history,
            current_season=current_season,
            season=season,
        )
    )

    played_matches = (
        count_played_matches(
            updated_history
        )
    )

    future_matches = (
        count_future_matches(
            updated_history
        )
    )

    print(
        f"[SUCCESS] Histórico preparado: "
        f"{played_matches} jogados | "
        f"{future_matches} futuros."
    )

    # =========================================================================
    # Machine Learning
    # =========================================================================

    artifacts = build_ml_artifacts(
        history=updated_history
    )

    # =========================================================================
    # Publicação
    # =========================================================================

    print()
    print("=" * 72)
    print("💾 PUBLICAÇÃO DOS ARTEFATOS")
    print("=" * 72)

    targets = (
        save_ml_artifacts_atomically(
            artifacts
        )
    )

    for name, path in (
        targets.items()
    ):

        print(
            f"[SUCCESS] {name}: {path}"
        )

    print()
    print("=" * 72)
    print(
        "✅ Machine Learning atualizado com sucesso."
    )
    print("=" * 72)
    print()

    return AutomatedMLUpdateResult(
        updated=True,
        check=check,
        played_matches=played_matches,
        future_matches=future_matches,
    )


# =============================================================================
# CLI
# =============================================================================


def main() -> None:
    """
    Permite executar diretamente com:

    python -m brasileirao_data_lab.pipelines.automated_ml_update
    """

    result = run_automated_ml_update()

    print()
    print(
        f"[RESULT] updated="
        f"{result.updated}"
    )

    print(
        f"[RESULT] played_matches="
        f"{result.played_matches}"
    )

    print(
        f"[RESULT] future_matches="
        f"{result.future_matches}"
    )

    print()


if __name__ == "__main__":
    main()