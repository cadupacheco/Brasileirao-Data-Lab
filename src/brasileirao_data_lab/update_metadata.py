from __future__ import annotations

import json

from dataclasses import (
    asdict,
    dataclass,
)
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_SOURCE = "CBF"
DEFAULT_CHECKS_PER_DAY = 4

VALID_MATCH_STATUSES = {
    "played",
    "upcoming",
}


# =============================================================================
# Modelo
# =============================================================================


@dataclass(
    frozen=True
)
class UpdateMetadata:
    """
    Metadados públicos sobre a versão atual
    dos dados do Brasileirão.
    """

    season: int
    source: str
    status: str

    last_sync_at_utc: str

    total_matches: int
    played_matches: int
    future_matches: int

    automation_enabled: bool
    checks_per_day: int


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """
    Retorna a raiz do projeto.
    """

    return (
        Path(
            __file__
        )
        .resolve()
        .parents[
            2
        ]
    )


def get_update_metadata_file() -> Path:
    """
    Retorna o arquivo oficial de metadata.
    """

    return (
        get_project_root()
        / "data"
        / "update_metadata.json"
    )


# =============================================================================
# Data/hora
# =============================================================================


def utc_now_iso() -> str:
    """
    Retorna o horário UTC atual em ISO 8601.

    Exemplo:
    2026-08-20T12:01:55Z
    """

    current = (
        datetime.now(
            timezone.utc
        )
        .replace(
            microsecond=0
        )
    )

    return (
        current
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


# =============================================================================
# Construção
# =============================================================================


def build_update_metadata(
    matches: pd.DataFrame,
    season: int,
    synced_at_utc: str | None = None,
    source: str = DEFAULT_SOURCE,
    checks_per_day: int = DEFAULT_CHECKS_PER_DAY,
) -> UpdateMetadata:
    """
    Constrói os metadados da versão atual
    dos dados.

    Este método não grava nenhum arquivo.
    """

    if matches.empty:
        raise ValueError(
            "Não é possível criar metadata "
            "a partir de um dataset vazio."
        )

    required_columns = {
        "season",
        "status",
    }

    missing_columns = (
        required_columns
        - set(
            matches.columns
        )
    )

    if missing_columns:
        missing = ", ".join(
            sorted(
                missing_columns
            )
        )

        raise ValueError(
            "Colunas obrigatórias ausentes: "
            f"{missing}"
        )

    season_matches = (
        matches[
            matches[
                "season"
            ] == season
        ]
        .copy()
        .reset_index(
            drop=True
        )
    )

    if season_matches.empty:
        raise ValueError(
            f"Nenhuma partida da temporada "
            f"{season} foi encontrada."
        )

    statuses = set(
        season_matches[
            "status"
        ]
        .dropna()
        .astype(
            str
        )
        .tolist()
    )

    invalid_statuses = (
        statuses
        - VALID_MATCH_STATUSES
    )

    if invalid_statuses:
        invalid = ", ".join(
            sorted(
                invalid_statuses
            )
        )

        raise ValueError(
            "Status de partida inválido: "
            f"{invalid}"
        )

    if season_matches[
        "status"
    ].isna().any():
        raise ValueError(
            "Existem partidas sem status."
        )

    total_matches = len(
        season_matches
    )

    played_matches = int(
        (
            season_matches[
                "status"
            ] == "played"
        ).sum()
    )

    future_matches = int(
        (
            season_matches[
                "status"
            ] == "upcoming"
        ).sum()
    )

    if (
        played_matches
        + future_matches
        != total_matches
    ):
        raise ValueError(
            "A soma de jogos disputados e futuros "
            "não corresponde ao total de partidas."
        )

    if checks_per_day <= 0:
        raise ValueError(
            "checks_per_day deve ser maior que zero."
        )

    timestamp = (
        synced_at_utc
        if synced_at_utc is not None
        else utc_now_iso()
    )

    return UpdateMetadata(
        season=season,
        source=source,
        status="up_to_date",
        last_sync_at_utc=timestamp,
        total_matches=total_matches,
        played_matches=played_matches,
        future_matches=future_matches,
        automation_enabled=True,
        checks_per_day=checks_per_day,
    )


# =============================================================================
# Serialização
# =============================================================================


def metadata_to_dict(
    metadata: UpdateMetadata,
) -> dict[str, Any]:
    """
    Converte UpdateMetadata para dicionário.
    """

    return asdict(
        metadata
    )


# =============================================================================
# Escrita
# =============================================================================


def save_update_metadata(
    metadata: UpdateMetadata,
    path: Path | None = None,
) -> Path:
    """
    Salva metadata em JSON UTF-8.
    """

    target = (
        path
        if path is not None
        else get_update_metadata_file()
    )

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with target.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:

        json.dump(
            metadata_to_dict(
                metadata
            ),
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write(
            "\n"
        )

    return target


# =============================================================================
# Leitura
# =============================================================================


def load_update_metadata(
    path: Path | None = None,
) -> UpdateMetadata:
    """
    Carrega metadata existente.
    """

    target = (
        path
        if path is not None
        else get_update_metadata_file()
    )

    if not target.exists():
        raise FileNotFoundError(
            f"Metadata não encontrada: "
            f"{target}"
        )

    with target.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(
            file
        )

    return UpdateMetadata(
        **payload
    )