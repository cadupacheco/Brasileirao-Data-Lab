from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from brasileirao_data_lab.scrapers.cbf_history import (
    build_history_dataframe,
    fetch_season_matches,
    get_history_output_file,
)


CURRENT_SEASON = 2026

TRACKED_COLUMNS = (
    "season",
    "competition_id",
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
    "status",
    "result",
)


@dataclass(frozen=True)
class MatchChange:
    match_id: int
    changed_fields: tuple[str, ...]
    previous: dict[str, Any]
    current: dict[str, Any]


@dataclass(frozen=True)
class UpdateCheckResult:
    has_changes: bool
    previous_count: int
    current_count: int
    new_match_ids: tuple[int, ...]
    removed_match_ids: tuple[int, ...]
    changed_matches: tuple[MatchChange, ...]
    newly_played_match_ids: tuple[int, ...]

    @property
    def changed_match_ids(self) -> tuple[int, ...]:
        return tuple(
            change.match_id
            for change in self.changed_matches
        )

    @property
    def total_changes(self) -> int:
        return (
            len(self.new_match_ids)
            + len(self.removed_match_ids)
            + len(self.changed_matches)
        )


def _normalize_scalar(value: Any) -> Any:
    """Normaliza valores para comparação estável entre snapshots."""
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass

    return value


def _validate_snapshot(
    dataframe: pd.DataFrame,
    label: str,
) -> None:
    """Valida a estrutura mínima necessária para comparar snapshots."""
    if dataframe.empty:
        raise ValueError(
            f"Snapshot {label} está vazio."
        )

    missing_columns = [
        column
        for column in TRACKED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Snapshot {label} não possui as colunas: "
            f"{', '.join(missing_columns)}."
        )

    duplicated_ids = int(
        dataframe["match_id"]
        .duplicated()
        .sum()
    )

    if duplicated_ids:
        raise ValueError(
            f"Snapshot {label} possui "
            f"{duplicated_ids} match_id duplicados."
        )


def _filter_season(
    dataframe: pd.DataFrame,
    season: int,
) -> pd.DataFrame:
    """Mantém somente a temporada escolhida."""
    filtered = (
        dataframe[
            dataframe["season"] == season
        ]
        .copy()
        .reset_index(drop=True)
    )

    if filtered.empty:
        raise ValueError(
            f"Nenhuma partida da temporada {season} "
            "foi encontrada no snapshot."
        )

    return filtered


def _row_to_dict(
    row: pd.Series,
) -> dict[str, Any]:
    """Converte uma linha em dicionário comparável."""
    return {
        column: _normalize_scalar(
            row[column]
        )
        for column in TRACKED_COLUMNS
    }


def _build_index(
    dataframe: pd.DataFrame,
) -> dict[int, dict[str, Any]]:
    """Indexa partidas pelo match_id."""
    return {
        int(row["match_id"]): _row_to_dict(row)
        for _, row in dataframe.iterrows()
    }


def compare_match_snapshots(
    previous: pd.DataFrame,
    current: pd.DataFrame,
    season: int = CURRENT_SEASON,
) -> UpdateCheckResult:
    """
    Compara dois snapshots da mesma temporada.

    Detecta novas partidas, partidas removidas,
    mudanças de placar/status e alterações de agenda.
    """
    previous_season = _filter_season(
        previous,
        season,
    )
    current_season = _filter_season(
        current,
        season,
    )

    _validate_snapshot(
        previous_season,
        "anterior",
    )
    _validate_snapshot(
        current_season,
        "atual",
    )

    previous_index = _build_index(
        previous_season
    )
    current_index = _build_index(
        current_season
    )

    previous_ids = set(previous_index)
    current_ids = set(current_index)

    new_match_ids = tuple(
        sorted(
            current_ids
            - previous_ids
        )
    )
    removed_match_ids = tuple(
        sorted(
            previous_ids
            - current_ids
        )
    )

    changed_matches: list[
        MatchChange
    ] = []
    newly_played_match_ids: list[
        int
    ] = []

    for match_id in sorted(
        previous_ids
        & current_ids
    ):
        previous_match = previous_index[
            match_id
        ]
        current_match = current_index[
            match_id
        ]

        changed_fields = tuple(
            column
            for column in TRACKED_COLUMNS
            if (
                previous_match[column]
                != current_match[column]
            )
        )

        if changed_fields:
            changed_matches.append(
                MatchChange(
                    match_id=match_id,
                    changed_fields=changed_fields,
                    previous=previous_match,
                    current=current_match,
                )
            )

        if (
            previous_match["status"]
            != "played"
            and current_match["status"]
            == "played"
        ):
            newly_played_match_ids.append(
                match_id
            )

    return UpdateCheckResult(
        has_changes=bool(
            new_match_ids
            or removed_match_ids
            or changed_matches
        ),
        previous_count=len(
            previous_season
        ),
        current_count=len(
            current_season
        ),
        new_match_ids=new_match_ids,
        removed_match_ids=removed_match_ids,
        changed_matches=tuple(
            changed_matches
        ),
        newly_played_match_ids=tuple(
            newly_played_match_ids
        ),
    )


def load_saved_history(
    history_file: Path | None = None,
) -> pd.DataFrame:
    """Carrega o histórico versionado atualmente."""
    selected_file = (
        history_file
        or get_history_output_file()
    )

    if not selected_file.exists():
        raise FileNotFoundError(
            "Arquivo histórico não encontrado: "
            f"{selected_file}"
        )

    return pd.read_csv(
        selected_file,
        encoding="utf-8-sig",
    )


def fetch_current_season_dataframe(
    season: int = CURRENT_SEASON,
    delay: float = 0.20,
) -> pd.DataFrame:
    """Coleta a temporada atual diretamente da CBF."""
    matches = fetch_season_matches(
        season=season,
        delay=delay,
    )

    return build_history_dataframe(
        matches
    )


def check_for_updates(
    season: int = CURRENT_SEASON,
    history_file: Path | None = None,
    delay: float = 0.20,
) -> UpdateCheckResult:
    """Compara o histórico salvo com o estado atual da CBF."""
    previous = load_saved_history(
        history_file=history_file
    )
    current = (
        fetch_current_season_dataframe(
            season=season,
            delay=delay,
        )
    )

    return compare_match_snapshots(
        previous=previous,
        current=current,
        season=season,
    )


def print_update_check(
    result: UpdateCheckResult,
) -> None:
    """Imprime um resumo legível da comparação."""
    print()
    print("=" * 72)
    print("🔎 DETECTOR DE ATUALIZAÇÕES")
    print("=" * 72)
    print(
        f"Snapshot anterior: "
        f"{result.previous_count} jogos"
    )
    print(
        f"Snapshot atual:    "
        f"{result.current_count} jogos"
    )

    if not result.has_changes:
        print()
        print(
            "[SUCCESS] Nenhuma alteração detectada."
        )
        print(
            "[INFO] O pipeline pesado não precisa ser executado."
        )
        print("=" * 72)
        print()
        return

    print()
    print(
        f"[INFO] Alterações detectadas: "
        f"{result.total_changes}"
    )
    print(
        f"[INFO] Novas partidas: "
        f"{len(result.new_match_ids)}"
    )
    print(
        f"[INFO] Partidas removidas: "
        f"{len(result.removed_match_ids)}"
    )
    print(
        f"[INFO] Partidas modificadas: "
        f"{len(result.changed_matches)}"
    )
    print(
        f"[INFO] Novos resultados finais: "
        f"{len(result.newly_played_match_ids)}"
    )

    if result.changed_matches:
        print()
        print("Partidas modificadas:")
        print("-" * 72)

        for change in result.changed_matches:
            fields = ", ".join(
                change.changed_fields
            )
            print(
                f"match_id={change.match_id} "
                f"| campos={fields}"
            )

    if result.newly_played_match_ids:
        print()
        print(
            "[IMPORTANT] Partidas que viraram 'played': "
            + ", ".join(
                str(match_id)
                for match_id
                in result.newly_played_match_ids
            )
        )

    print()
    print(
        "[INFO] Uma atualização completa será necessária."
    )
    print("=" * 72)
    print()