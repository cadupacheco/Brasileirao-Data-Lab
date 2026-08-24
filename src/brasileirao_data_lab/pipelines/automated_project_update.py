from __future__ import annotations

import os
import shutil
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from brasileirao_data_lab.analytics.championship import get_matches_file
from brasileirao_data_lab.database.config import get_default_database_file
from brasileirao_data_lab.database.session import (
    create_database_engine,
    create_session_factory,
)
from brasileirao_data_lab.ml.features import get_features_file
from brasileirao_data_lab.ml.predictions import get_predictions_file
from brasileirao_data_lab.ml.simulation import get_simulation_file
from brasileirao_data_lab.pipelines.automated_ml_update import (
    EXPECTED_CURRENT_SEASON_MATCHES,
    MLArtifacts,
    build_ml_artifacts,
    build_updated_history,
)
from brasileirao_data_lab.pipelines.update_data import sync_and_validate_database
from brasileirao_data_lab.pipelines.update_detector import (
    CURRENT_SEASON,
    UpdateCheckResult,
    compare_match_snapshots,
    fetch_current_season_dataframe,
    load_saved_history,
    print_update_check,
)
from brasileirao_data_lab.scrapers.cbf_history import get_history_output_file


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

PLAYER_COLUMNS = (
    "player_id",
    "full_name",
    "nickname",
    "birth_date",
    "profile_url",
    "current_club_id",
    "current_club_name",
    "current_club_state",
    "current_club_badge_url",
)

PLAYER_STATS_COLUMNS = (
    "season",
    "competition_id",
    "player_id",
    "team_id",
    "competition_name",
    "category",
    "matches",
    "goals",
    "yellow_cards",
    "red_cards",
)


# =============================================================================
# Resultados
# =============================================================================


@dataclass(frozen=True)
class ProjectArtifacts:
    """
    Artefatos necessários para atualizar
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


@dataclass(frozen=True)
class PlayerDataPreservationResult:
    """
    Quantidade de dados de jogadores
    preservados no novo SQLite.
    """

    players: int
    player_stats: int


# =============================================================================
# Partidas utilizadas pelo banco/API
# =============================================================================


def build_processed_matches_dataframe(
    current_season: pd.DataFrame,
    season: int = CURRENT_SEASON,
    expected_matches: int = EXPECTED_CURRENT_SEASON_MATCHES,
) -> pd.DataFrame:
    """
    Converte o snapshot histórico
    para o formato de matches.csv.
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
# Preservação dos dados de jogadores
# =============================================================================


def sqlite_table_exists(
    connection: sqlite3.Connection,
    table_name: str,
) -> bool:
    """
    Verifica se uma tabela existe.
    """

    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        LIMIT 1
        """,
        (
            table_name,
        ),
    ).fetchone()

    return row is not None


def sqlite_table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> tuple[str, ...]:
    """
    Retorna as colunas de uma tabela.
    """

    rows = connection.execute(
        f'PRAGMA table_info("{table_name}")'
    ).fetchall()

    return tuple(
        str(
            row[1]
        )
        for row in rows
    )


def validate_preserved_table_schema(
    connection: sqlite3.Connection,
    table_name: str,
    expected_columns: tuple[str, ...],
    database_label: str,
) -> None:
    """
    Valida se a tabela possui todas
    as colunas necessárias.
    """

    if not sqlite_table_exists(
        connection,
        table_name,
    ):
        raise ValueError(
            f"Tabela {table_name!r} "
            f"não existe no banco "
            f"{database_label}."
        )

    available_columns = set(
        sqlite_table_columns(
            connection,
            table_name,
        )
    )

    missing_columns = [
        column
        for column in expected_columns
        if column not in available_columns
    ]

    if missing_columns:
        raise ValueError(
            f"Tabela {table_name!r} "
            f"do banco {database_label} "
            "não possui as colunas: "
            + ", ".join(
                missing_columns
            )
        )


def fetch_sqlite_rows(
    connection: sqlite3.Connection,
    table_name: str,
    columns: tuple[str, ...],
) -> list[tuple]:
    """
    Lê somente as colunas autorizadas.
    """

    columns_sql = ", ".join(
        f'"{column}"'
        for column in columns
    )

    rows = connection.execute(
        f'SELECT {columns_sql} '
        f'FROM "{table_name}"'
    ).fetchall()

    return [
        tuple(
            row
        )
        for row in rows
    ]


def insert_sqlite_rows(
    connection: sqlite3.Connection,
    table_name: str,
    columns: tuple[str, ...],
    rows: list[tuple],
) -> None:
    """
    Insere registros em uma tabela.
    """

    if not rows:
        return

    columns_sql = ", ".join(
        f'"{column}"'
        for column in columns
    )

    placeholders = ", ".join(
        "?"
        for _ in columns
    )

    connection.executemany(
        (
            f'INSERT INTO "{table_name}" '
            f"({columns_sql}) "
            f"VALUES ({placeholders})"
        ),
        rows,
    )


def count_sqlite_rows(
    connection: sqlite3.Connection,
    table_name: str,
) -> int:
    """
    Conta registros de uma tabela.
    """

    row = connection.execute(
        f'SELECT COUNT(*) '
        f'FROM "{table_name}"'
    ).fetchone()

    if row is None:
        return 0

    return int(
        row[0]
    )


def preserve_player_database_data(
    source_database_file: Path,
    target_database_file: Path,
) -> PlayerDataPreservationResult:
    """
    Preserva somente os dados
    pertencentes à feature de jogadores.

    O updater continua reconstruindo:

    - teams
    - matches
    - standings_snapshots

    E preserva:

    - players
    - player_team_competition_stats

    Se o banco antigo ainda for de uma
    versão anterior à V1.0 e não possuir
    essas tabelas, nenhuma cópia é feita.
    """

    source_database_file = Path(
        source_database_file
    ).resolve()

    target_database_file = Path(
        target_database_file
    ).resolve()

    if (
        source_database_file
        == target_database_file
    ):
        raise ValueError(
            "Banco de origem e banco "
            "temporário não podem ser "
            "o mesmo arquivo."
        )

    if not source_database_file.exists():
        print(
            "[INFO] Banco anterior não existe. "
            "Nenhum jogador será preservado."
        )

        return (
            PlayerDataPreservationResult(
                players=0,
                player_stats=0,
            )
        )

    if not target_database_file.exists():
        raise FileNotFoundError(
            "Banco temporário não encontrado: "
            f"{target_database_file}"
        )

    with closing(
        sqlite3.connect(
            source_database_file
        )
    ) as source_connection, closing(
        sqlite3.connect(
            target_database_file
        )
    ) as target_connection:

        source_has_players = (
            sqlite_table_exists(
                source_connection,
                "players",
            )
        )

        source_has_stats = (
            sqlite_table_exists(
                source_connection,
                "player_team_competition_stats",
            )
        )

        if (
            not source_has_players
            and not source_has_stats
        ):
            print(
                "[INFO] Banco anterior não possui "
                "tabelas de jogadores. "
                "Nada será preservado."
            )

            return (
                PlayerDataPreservationResult(
                    players=0,
                    player_stats=0,
                )
            )

        if (
            source_has_stats
            and not source_has_players
        ):
            raise ValueError(
                "Banco anterior possui "
                "estatísticas de jogadores, "
                "mas não possui a tabela players."
            )

        # ---------------------------------------------------------------------
        # Banco temporário
        # ---------------------------------------------------------------------

        validate_preserved_table_schema(
            target_connection,
            "players",
            PLAYER_COLUMNS,
            "temporário",
        )

        validate_preserved_table_schema(
            target_connection,
            "player_team_competition_stats",
            PLAYER_STATS_COLUMNS,
            "temporário",
        )

        # ---------------------------------------------------------------------
        # Banco anterior
        # ---------------------------------------------------------------------

        if source_has_players:
            validate_preserved_table_schema(
                source_connection,
                "players",
                PLAYER_COLUMNS,
                "anterior",
            )

        if source_has_stats:
            validate_preserved_table_schema(
                source_connection,
                "player_team_competition_stats",
                PLAYER_STATS_COLUMNS,
                "anterior",
            )

        # ---------------------------------------------------------------------
        # Segurança
        # ---------------------------------------------------------------------

        target_players_before = (
            count_sqlite_rows(
                target_connection,
                "players",
            )
        )

        target_stats_before = (
            count_sqlite_rows(
                target_connection,
                "player_team_competition_stats",
            )
        )

        if (
            target_players_before != 0
            or target_stats_before != 0
        ):
            raise ValueError(
                "Banco temporário deveria "
                "estar sem dados de jogadores "
                "antes da preservação. "
                f"players={target_players_before}, "
                f"stats={target_stats_before}."
            )

        # ---------------------------------------------------------------------
        # Snapshot dos jogadores
        # ---------------------------------------------------------------------

        player_rows = (
            fetch_sqlite_rows(
                source_connection,
                "players",
                PLAYER_COLUMNS,
            )
            if source_has_players
            else []
        )

        player_stats_rows = (
            fetch_sqlite_rows(
                source_connection,
                "player_team_competition_stats",
                PLAYER_STATS_COLUMNS,
            )
            if source_has_stats
            else []
        )

        print()

        print(
            "[INFO] Preservando dados "
            "de jogadores no novo SQLite..."
        )

        print(
            f"[INFO] Players no banco anterior: "
            f"{len(player_rows)}"
        )

        print(
            "[INFO] Stats jogador/clube "
            "no banco anterior: "
            f"{len(player_stats_rows)}"
        )

        # ---------------------------------------------------------------------
        # Cópia atômica
        # ---------------------------------------------------------------------

        target_connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        try:
            target_connection.execute(
                "BEGIN"
            )

            insert_sqlite_rows(
                target_connection,
                "players",
                PLAYER_COLUMNS,
                player_rows,
            )

            insert_sqlite_rows(
                target_connection,
                "player_team_competition_stats",
                PLAYER_STATS_COLUMNS,
                player_stats_rows,
            )

            target_connection.commit()

        except Exception:
            target_connection.rollback()

            raise

        # ---------------------------------------------------------------------
        # Validação final
        # ---------------------------------------------------------------------

        preserved_players = (
            count_sqlite_rows(
                target_connection,
                "players",
            )
        )

        preserved_stats = (
            count_sqlite_rows(
                target_connection,
                "player_team_competition_stats",
            )
        )

        if preserved_players != len(
            player_rows
        ):
            raise ValueError(
                "Falha ao preservar players. "
                f"Esperado: {len(player_rows)}. "
                f"Obtido: {preserved_players}."
            )

        if preserved_stats != len(
            player_stats_rows
        ):
            raise ValueError(
                "Falha ao preservar "
                "estatísticas de jogadores. "
                f"Esperado: "
                f"{len(player_stats_rows)}. "
                f"Obtido: {preserved_stats}."
            )

        print(
            f"[SUCCESS] Players preservados: "
            f"{preserved_players}"
        )

        print(
            "[SUCCESS] Stats jogador/clube "
            f"preservadas: {preserved_stats}"
        )

        return (
            PlayerDataPreservationResult(
                players=preserved_players,
                player_stats=preserved_stats,
            )
        )


# =============================================================================
# Banco temporário
# =============================================================================


def build_database_file(
    matches: pd.DataFrame,
    database_file: Path,
    source_database_file: Path | None = None,
) -> Path:
    """
    Cria e valida um SQLite novo.

    Se source_database_file for informado,
    os dados de jogadores são copiados
    somente depois que as partidas forem
    reconstruídas e validadas.
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
        (
            sync_result,
            validation_result,
        ) = sync_and_validate_database(
            matches=matches,
            database_engine=database_engine,
            session_factory=session_factory,
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
                "Quantidade de partidas "
                "no banco temporário "
                "está incorreta."
            )

        print(
            "[SUCCESS] Banco temporário "
            f"validado: {database_count} partidas."
        )

        del sync_result

    finally:
        database_engine.dispose()

    if not database_file.exists():
        raise FileNotFoundError(
            "O banco temporário "
            "não foi criado."
        )

    if source_database_file is not None:
        preserve_player_database_data(
            source_database_file=(
                source_database_file
            ),
            target_database_file=(
                database_file
            ),
        )

    return database_file


# =============================================================================
# Caminhos oficiais
# =============================================================================


def get_project_targets() -> dict[str, Path]:
    """
    Retorna os arquivos oficiais
    atualizados quando a CBF muda.
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
    Salva DataFrame em UTF-8 com BOM.
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
# Construção dos artefatos
# =============================================================================


def build_project_artifacts(
    previous_history: pd.DataFrame,
    current_season: pd.DataFrame,
    season: int = CURRENT_SEASON,
) -> ProjectArtifacts:
    """
    Constrói os novos artefatos
    primeiro em memória.
    """

    print()

    print(
        "=" * 72
    )

    print(
        "🏗️ PREPARANDO NOVA VERSÃO DOS DADOS"
    )

    print(
        "=" * 72
    )

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
        "[SUCCESS] Dataset principal "
        f"preparado: "
        f"{len(processed_matches)} jogos."
    )

    ml_artifacts = (
        build_ml_artifacts(
            history=updated_history
        )
    )

    return ProjectArtifacts(
        processed_matches=(
            processed_matches
        ),
        ml=ml_artifacts,
    )


# =============================================================================
# Publicação atômica
# =============================================================================


def publish_project_artifacts(
    artifacts: ProjectArtifacts,
) -> dict[str, Path]:
    """
    Publica os artefatos de forma atômica.

    O banco novo:

    1. é reconstruído;
    2. é validado;
    3. recebe os jogadores do banco atual;
    4. é validado novamente;
    5. substitui o banco oficial.

    Se algo falhar na publicação,
    os arquivos anteriores são restaurados.
    """

    targets = (
        get_project_targets()
    )

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
        # Matches
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
        # Histórico
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
        # SQLite
        # =====================================================================

        staged_database = (
            temporary_path
            / "brasileirao.db"
        )

        build_database_file(
            matches=(
                artifacts
                .processed_matches
            ),
            database_file=(
                staged_database
            ),
            source_database_file=(
                targets[
                    "database"
                ]
            ),
        )

        staged_files[
            "database"
        ] = staged_database

        # =====================================================================
        # Backups
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
                target = (
                    targets[
                        name
                    ]
                )

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
                "[INFO] Restaurando "
                "arquivos anteriores..."
            )

            for name in reversed(
                replaced_files
            ):
                target = (
                    targets[
                        name
                    ]
                )

                backup = (
                    backup_files.get(
                        name
                    )
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
# Pipeline automático
# =============================================================================


def run_automated_project_update(
    season: int = CURRENT_SEASON,
    delay: float = 0.20,
) -> AutomatedProjectUpdateResult:
    """
    Executa o pipeline automático completo.
    """

    print()

    print(
        "⚽ Brasileirão Data Lab"
    )

    print(
        "⚙️ Atualização automática V0.7"
    )

    print(
        "=" * 72
    )

    # =========================================================================
    # Histórico atual
    # =========================================================================

    print()

    print(
        "[INFO] Carregando histórico atual..."
    )

    previous_history = (
        load_saved_history()
    )

    print(
        "[SUCCESS] "
        f"{len(previous_history)} "
        "partidas carregadas."
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
            "[SUCCESS] Projeto "
            "já está atualizado."
        )

        print(
            "[INFO] Nenhum arquivo "
            "será alterado."
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
    # Mudança detectada
    # =========================================================================

    print()

    print(
        "[IMPORTANT] Mudança detectada."
    )

    print(
        "[INFO] Iniciando "
        "reconstrução completa..."
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

    print(
        "=" * 72
    )

    print(
        "🚀 PUBLICANDO NOVA VERSÃO DOS DADOS"
    )

    print(
        "=" * 72
    )

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

    print(
        "=" * 72
    )

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

    print(
        "=" * 72
    )

    print()

    return (
        AutomatedProjectUpdateResult(
            updated=True,
            check=check,
            played_matches=played_matches,
            future_matches=future_matches,
        )
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