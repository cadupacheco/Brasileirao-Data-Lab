from __future__ import annotations

import os
import shutil

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from brasileirao_data_lab.analytics.championship import (
    get_matches_file,
)
from brasileirao_data_lab.database.config import (
    get_default_database_file,
)
from brasileirao_data_lab.database.session import (
    create_database_engine,
    create_session_factory,
)
from brasileirao_data_lab.ml.features import (
    get_features_file,
)
from brasileirao_data_lab.ml.predictions import (
    get_predictions_file,
)
from brasileirao_data_lab.ml.simulation import (
    get_simulation_file,
)
from brasileirao_data_lab.pipelines.automated_ml_update import (
    EXPECTED_CURRENT_SEASON_MATCHES,
    MLArtifacts,
    build_ml_artifacts,
    build_updated_history,
)
from brasileirao_data_lab.pipelines.update_data import (
    sync_and_validate_database,
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
)


PROCESSED_MATCH_COLUMNS = [
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


# =============================================================================
# Resultado
# =============================================================================


@dataclass(frozen=True)
class ProjectArtifacts:
    """
    Todos os dados necessários para atualizar
    backend, dashboard e Machine Learning.
    """

    processed_matches: pd.DataFrame
    ml: MLArtifacts


@dataclass(frozen=True)
class AutomatedProjectUpdateResult:
    """
    Resultado final da atualização automática.
    """

    updated: bool
    check: UpdateCheckResult
    played_matches: int
    future_matches: int


# =============================================================================
# Partidas utilizadas pelo banco/API
# =============================================================================


def build_processed_matches_dataframe(
    current_season: pd.DataFrame,
    season: int = CURRENT_SEASON,
    expected_matches: int = EXPECTED_CURRENT_SEASON_MATCHES,
) -> pd.DataFrame:
    """
    Converte o formato histórico da V0.6 para o formato
    utilizado por data/processed/matches.csv e pelo SQLite.
    """

    if current_season.empty:
        raise ValueError(
            "Snapshot da temporada atual está vazio."
        )

    season_data = (
        current_season[
            current_season[
                "season"
            ] == season
        ]
        .copy()
    )

    if len(
        season_data
    ) != expected_matches:
        raise ValueError(
            f"Temporada {season}: esperado "
            f"{expected_matches} jogos, "
            f"recebidos {len(season_data)}."
        )

    missing_columns = [
        column
        for column in PROCESSED_MATCH_COLUMNS
        if column not in season_data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Snapshot não possui as colunas necessárias: "
            + ", ".join(
                missing_columns
            )
        )

    processed = (
        season_data[
            PROCESSED_MATCH_COLUMNS
        ]
        .copy()
        .sort_values(
            by=[
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

    if processed[
        "match_id"
    ].duplicated().any():
        raise ValueError(
            "Existem match_id duplicados "
            "nas partidas processadas."
        )

    return processed


# =============================================================================
# Banco temporário
# =============================================================================


def build_database_file(
    matches: pd.DataFrame,
    database_file: Path,
) -> Path:
    """
    Cria um SQLite novo em um caminho temporário.

    O banco oficial ainda não é alterado.

    O próprio pipeline existente executa:
    - criação das tabelas;
    - sincronização;
    - validação;
    - commit somente se tudo estiver correto.
    """

    database_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if database_file.exists():
        database_file.unlink()

    database_url = (
        "sqlite:///"
        + database_file
        .resolve()
        .as_posix()
    )

    database_engine = (
        create_database_engine(
            database_url
        )
    )

    session_factory = (
        create_session_factory(
            database_engine
        )
    )

    try:

        sync_result, validation_result = (
            sync_and_validate_database(
                matches=matches,
                database_engine=database_engine,
                session_factory=session_factory,
            )
        )

        if not validation_result[
            "exact_match"
        ]:
            raise ValueError(
                "Banco temporário não corresponde "
                "ao dataset processado."
            )

        database_count = int(
            validation_result[
                "database_count"
            ]
        )

        if database_count != len(
            matches
        ):
            raise ValueError(
                "Quantidade de partidas no banco "
                "temporário está incorreta."
            )

        print(
            f"[SUCCESS] Banco temporário validado: "
            f"{database_count} partidas."
        )

        del sync_result

    finally:

        database_engine.dispose()

    if not database_file.exists():
        raise FileNotFoundError(
            "O banco temporário não foi criado."
        )

    return database_file


# =============================================================================
# Caminhos oficiais
# =============================================================================


def get_project_targets() -> dict[str, Path]:
    """
    Retorna todos os arquivos que serão atualizados
    quando houver mudança na CBF.
    """

    return {
        "matches": (
            get_matches_file()
        ),
        "database": (
            get_default_database_file()
        ),
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
# Escrita CSV
# =============================================================================


def save_dataframe(
    dataframe: pd.DataFrame,
    path: Path,
) -> Path:
    """
    Salva DataFrame em CSV.
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

    return path


# =============================================================================
# Construção completa
# =============================================================================


def build_project_artifacts(
    previous_history: pd.DataFrame,
    current_season: pd.DataFrame,
    season: int = CURRENT_SEASON,
) -> ProjectArtifacts:
    """
    Constrói tudo primeiro em memória.

    Nenhum arquivo oficial é alterado aqui.
    """

    print()
    print("=" * 72)
    print("🏗️ PREPARANDO NOVA VERSÃO DOS DADOS")
    print("=" * 72)

    updated_history = (
        build_updated_history(
            previous_history=previous_history,
            current_season=current_season,
            season=season,
        )
    )

    processed_matches = (
        build_processed_matches_dataframe(
            current_season=current_season,
            season=season,
        )
    )

    print()
    print(
        f"[SUCCESS] Dataset principal preparado: "
        f"{len(processed_matches)} jogos."
    )

    ml_artifacts = (
        build_ml_artifacts(
            history=updated_history
        )
    )

    return ProjectArtifacts(
        processed_matches=processed_matches,
        ml=ml_artifacts,
    )


# =============================================================================
# Publicação atômica
# =============================================================================


def publish_project_artifacts(
    artifacts: ProjectArtifacts,
) -> dict[str, Path]:
    """
    Publica todos os arquivos de uma só vez.

    Antes de alterar o projeto:

    1. cria todos os CSVs em diretório temporário;
    2. cria um banco SQLite temporário;
    3. valida o banco;
    4. cria backup dos arquivos atuais;
    5. substitui os arquivos oficiais.

    Se algo falhar durante a substituição,
    os backups são restaurados.
    """

    targets = get_project_targets()

    project_root = (
        get_default_database_file()
        .parent
        .parent
    )

    with TemporaryDirectory(
        prefix=".v07-project-update-",
        dir=project_root,
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
        # CSV principal
        # =====================================================================

        staged_matches = (
            temporary_path
            / "matches.csv"
        )

        save_dataframe(
            artifacts.processed_matches,
            staged_matches,
        )

        staged_files[
            "matches"
        ] = staged_matches

        # =====================================================================
        # Histórico ML
        # =====================================================================

        staged_history = (
            temporary_path
            / "matches_history.csv"
        )

        save_dataframe(
            artifacts.ml.history,
            staged_history,
        )

        staged_files[
            "history"
        ] = staged_history

        # =====================================================================
        # Features
        # =====================================================================

        staged_features = (
            temporary_path
            / "features.csv"
        )

        save_dataframe(
            artifacts.ml.features,
            staged_features,
        )

        staged_files[
            "features"
        ] = staged_features

        # =====================================================================
        # Previsões
        # =====================================================================

        staged_predictions = (
            temporary_path
            / "future_predictions.csv"
        )

        save_dataframe(
            artifacts.ml.predictions,
            staged_predictions,
        )

        staged_files[
            "predictions"
        ] = staged_predictions

        # =====================================================================
        # Monte Carlo
        # =====================================================================

        staged_simulation = (
            temporary_path
            / "season_simulation.csv"
        )

        save_dataframe(
            artifacts.ml.simulation,
            staged_simulation,
        )

        staged_files[
            "simulation"
        ] = staged_simulation

        # =====================================================================
        # Banco
        # =====================================================================

        staged_database = (
            temporary_path
            / "brasileirao.db"
        )

        build_database_file(
            matches=artifacts.processed_matches,
            database_file=staged_database,
        )

        staged_files[
            "database"
        ] = staged_database

        # =====================================================================
        # Backup
        # =====================================================================

        for name, target in (
            targets.items()
        ):

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if not target.exists():
                continue

            backup_file = (
                temporary_path
                / f"{name}.backup"
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

            for name in (
                "matches",
                "database",
                "history",
                "features",
                "predictions",
                "simulation",
            ):

                target = targets[
                    name
                ]

                staged_file = (
                    staged_files[
                        name
                    ]
                )

                os.replace(
                    staged_file,
                    target,
                )

                replaced_files.append(
                    name
                )

        except Exception:

            print()
            print(
                "[ERROR] Falha durante publicação."
            )

            print(
                "[INFO] Restaurando arquivos anteriores..."
            )

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

            print(
                "[SUCCESS] Rollback concluído."
            )

            raise

    return targets


# =============================================================================
# Pipeline automático completo
# =============================================================================


def run_automated_project_update(
    season: int = CURRENT_SEASON,
    delay: float = 0.20,
) -> AutomatedProjectUpdateResult:
    """
    Pipeline principal da V0.7.

    Fluxo:

    CBF
      ↓
    detector
      ↓
    nada mudou -> encerra
      ↓
    mudou
      ↓
    novo histórico
      ↓
    matches.csv
      ↓
    features
      ↓
    Random Forest
      ↓
    previsões
      ↓
    Monte Carlo
      ↓
    novo SQLite
      ↓
    validação
      ↓
    publicação
    """

    print()
    print("⚽ Brasileirão Data Lab")
    print("⚙️ Atualização automática V0.7")
    print("=" * 72)

    # =========================================================================
    # Snapshot anterior
    # =========================================================================

    print()
    print(
        "[INFO] Carregando histórico atual..."
    )

    previous_history = (
        load_saved_history()
    )

    print(
        f"[SUCCESS] "
        f"{len(previous_history)} partidas carregadas."
    )

    # =========================================================================
    # CBF
    # =========================================================================

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

    # =========================================================================
    # Detector
    # =========================================================================

    check = (
        compare_match_snapshots(
            previous=previous_history,
            current=current_season,
            season=season,
        )
    )

    print_update_check(
        check
    )

    # =========================================================================
    # Nada mudou
    # =========================================================================

    if not check.has_changes:

        season_history = (
            previous_history[
                previous_history[
                    "season"
                ] == season
            ]
        )

        played_matches = int(
            (
                season_history[
                    "status"
                ] == "played"
            ).sum()
        )

        future_matches = int(
            (
                season_history[
                    "status"
                ] == "upcoming"
            ).sum()
        )

        print(
            "[SUCCESS] Projeto já está atualizado."
        )

        print(
            "[INFO] Nenhum arquivo será alterado."
        )

        return (
            AutomatedProjectUpdateResult(
                updated=False,
                check=check,
                played_matches=played_matches,
                future_matches=future_matches,
            )
        )

    # =========================================================================
    # Mudou
    # =========================================================================

    print()
    print(
        "[IMPORTANT] Mudança detectada."
    )

    print(
        "[INFO] Iniciando reconstrução completa..."
    )

    artifacts = (
        build_project_artifacts(
            previous_history=previous_history,
            current_season=current_season,
            season=season,
        )
    )

    season_history = (
        artifacts
        .ml
        .history[
            artifacts
            .ml
            .history[
                "season"
            ] == season
        ]
    )

    played_matches = int(
        (
            season_history[
                "status"
            ] == "played"
        ).sum()
    )

    future_matches = int(
        (
            season_history[
                "status"
            ] == "upcoming"
        ).sum()
    )

    # =========================================================================
    # Publicação
    # =========================================================================

    print()
    print("=" * 72)
    print("🚀 PUBLICANDO NOVA VERSÃO DOS DADOS")
    print("=" * 72)

    targets = (
        publish_project_artifacts(
            artifacts
        )
    )

    print()

    for name, path in (
        targets.items()
    ):

        print(
            f"[SUCCESS] {name}: {path}"
        )

    print()
    print("=" * 72)

    print(
        "✅ Projeto atualizado com sucesso."
    )

    print(
        f"[INFO] Jogos disputados: "
        f"{played_matches}"
    )

    print(
        f"[INFO] Jogos futuros: "
        f"{future_matches}"
    )

    print("=" * 72)
    print()

    return AutomatedProjectUpdateResult(
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
    Execução via:

    python -m brasileirao_data_lab.pipelines.automated_project_update
    """

    result = (
        run_automated_project_update()
    )

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