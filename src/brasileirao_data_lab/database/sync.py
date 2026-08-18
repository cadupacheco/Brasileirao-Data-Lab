from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from brasileirao_data_lab.analytics.championship import (
    get_teams,
    load_matches,
)
from brasileirao_data_lab.analytics.evolution import (
    get_position_history,
)
from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.database.models import (
    Match,
    StandingsSnapshot,
    Team,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
    engine,
)


# =============================================================================
# Conversão de valores
# =============================================================================


def is_missing(
    value: Any,
) -> bool:
    """Retorna True para valores ausentes do Pandas."""

    if value is None:
        return True

    try:

        result = pd.isna(
            value
        )

        if isinstance(
            result,
            bool,
        ):

            return result

    except (TypeError, ValueError):

        pass

    return False


def optional_text(
    value: Any,
) -> str | None:
    """Converte um valor opcional para texto."""

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


def optional_int(
    value: Any,
) -> int | None:
    """Converte um valor opcional para inteiro."""

    if is_missing(
        value
    ):
        return None

    return int(
        value
    )


def optional_date(
    value: Any,
) -> date | None:
    """Converte um valor opcional para datetime.date."""

    if is_missing(
        value
    ):
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    if isinstance(
        value,
        date,
    ):
        return value

    parsed = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(
        parsed
    ):
        return None

    return parsed.date()


def optional_time(
    value: Any,
) -> time | None:
    """Converte um horário opcional para datetime.time."""

    if is_missing(
        value
    ):
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.time().replace(
            microsecond=0
        )

    if isinstance(
        value,
        time,
    ):
        return value.replace(
            microsecond=0
        )

    text = str(
        value
    ).strip()

    if not text:
        return None

    parsed = pd.to_datetime(
        text,
        format="%H:%M",
        errors="coerce",
    )

    if pd.isna(
        parsed
    ):

        parsed = pd.to_datetime(
            text,
            errors="coerce",
        )

    if pd.isna(
        parsed
    ):
        return None

    return parsed.time().replace(
        microsecond=0
    )


# =============================================================================
# Temporada
# =============================================================================


def infer_season(
    matches: pd.DataFrame,
) -> int:
    """
    Descobre a temporada presente no dataset.

    O sincronizador trabalha com uma temporada
    por execução.
    """

    if "season" not in matches.columns:

        raise ValueError(
            "O dataset de partidas não possui "
            "a coluna 'season'."
        )

    seasons = (
        pd.to_numeric(
            matches["season"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    if not seasons:

        raise ValueError(
            "Nenhuma temporada válida foi "
            "encontrada no dataset."
        )

    if len(
        seasons
    ) != 1:

        raise ValueError(
            "O sincronizador aceita apenas "
            "uma temporada por execução. "
            f"Encontradas: {sorted(seasons)}"
        )

    return int(
        seasons[0]
    )


# =============================================================================
# Resultado de sincronização
# =============================================================================


def create_sync_result() -> dict[str, int]:
    """Cria o contador padrão de sincronização."""

    return {
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
    }


# =============================================================================
# Times
# =============================================================================


def sync_teams(
    session: Session,
    matches: pd.DataFrame,
) -> dict[str, int]:
    """
    Insere ou atualiza os clubes encontrados
    no dataset de partidas.
    """

    result = create_sync_result()

    teams = get_teams(
        matches
    )

    for _, row in teams.iterrows():

        team_id = int(
            row["team_id"]
        )

        name = str(
            row["team"]
        ).strip()

        existing = session.get(
            Team,
            team_id,
        )

        if existing is None:

            session.add(
                Team(
                    team_id=team_id,
                    name=name,
                )
            )

            result[
                "inserted"
            ] += 1

            continue

        if existing.name != name:

            existing.name = name

            result[
                "updated"
            ] += 1

        else:

            result[
                "unchanged"
            ] += 1

    session.flush()

    return result


# =============================================================================
# Partidas
# =============================================================================


def row_to_match_values(
    row: pd.Series,
) -> dict[str, Any]:
    """
    Converte uma linha do DataFrame
    para os campos do modelo Match.
    """

    return {
        "season": int(
            row["season"]
        ),
        "round": int(
            row["round"]
        ),
        "match_number": optional_int(
            row.get(
                "match_number"
            )
        ),
        "group": optional_text(
            row.get(
                "group"
            )
        ),
        "date": optional_date(
            row.get(
                "date"
            )
        ),
        "time": optional_time(
            row.get(
                "time"
            )
        ),
        "home_team_id": int(
            row[
                "home_team_id"
            ]
        ),
        "home_goals": optional_int(
            row.get(
                "home_goals"
            )
        ),
        "away_team_id": int(
            row[
                "away_team_id"
            ]
        ),
        "away_goals": optional_int(
            row.get(
                "away_goals"
            )
        ),
        "venue": optional_text(
            row.get(
                "venue"
            )
        ),
        "city": optional_text(
            row.get(
                "city"
            )
        ),
        "state": optional_text(
            row.get(
                "state"
            )
        ),
        "championship": optional_text(
            row.get(
                "championship"
            )
        ),
    }


def update_model_fields(
    instance: Any,
    values: dict[str, Any],
) -> bool:
    """
    Atualiza os campos que mudaram.

    Retorna True se pelo menos um campo
    foi alterado.
    """

    changed = False

    for field_name, new_value in (
        values.items()
    ):

        old_value = getattr(
            instance,
            field_name,
        )

        if old_value != new_value:

            setattr(
                instance,
                field_name,
                new_value,
            )

            changed = True

    return changed


def sync_matches(
    session: Session,
    matches: pd.DataFrame,
) -> dict[str, int]:
    """
    Insere ou atualiza partidas.

    match_id é utilizado como identidade
    permanente da partida.
    """

    result = create_sync_result()

    for _, row in matches.iterrows():

        match_id = int(
            row["match_id"]
        )

        values = row_to_match_values(
            row
        )

        existing = session.get(
            Match,
            match_id,
        )

        if existing is None:

            session.add(
                Match(
                    match_id=match_id,
                    **values,
                )
            )

            result[
                "inserted"
            ] += 1

            continue

        changed = update_model_fields(
            existing,
            values,
        )

        if changed:

            result[
                "updated"
            ] += 1

        else:

            result[
                "unchanged"
            ] += 1

    session.flush()

    return result


# =============================================================================
# Snapshots
# =============================================================================


def row_to_snapshot_values(
    row: pd.Series,
    season: int,
) -> dict[str, Any]:
    """
    Converte uma linha do histórico de posição
    para um StandingsSnapshot.
    """

    matches_played = int(
        row["matches"]
    )

    points = int(
        row["points"]
    )

    maximum_points = (
        matches_played * 3
    )

    performance_pct = (
        points
        / maximum_points
        * 100
        if maximum_points
        else 0.0
    )

    return {
        "season": season,
        "round": int(
            row["round"]
        ),
        "team_id": int(
            row["team_id"]
        ),
        "position": int(
            row["position"]
        ),
        "matches": matches_played,
        "wins": int(
            row["wins"]
        ),
        "draws": int(
            row["draws"]
        ),
        "losses": int(
            row["losses"]
        ),
        "goals_for": int(
            row["goals_for"]
        ),
        "goals_against": int(
            row["goals_against"]
        ),
        "goal_difference": int(
            row[
                "goal_difference"
            ]
        ),
        "points": points,
        "performance_pct": round(
            performance_pct,
            2,
        ),
    }


def sync_standings_snapshots(
    session: Session,
    matches: pd.DataFrame,
) -> dict[str, int]:
    """
    Reconstrói e sincroniza a classificação
    rodada por rodada.
    """

    result = create_sync_result()

    season = infer_season(
        matches
    )

    history = get_position_history(
        matches
    )

    if history.empty:
        return result

    for _, row in history.iterrows():

        values = row_to_snapshot_values(
            row,
            season,
        )

        identity = (
            values["season"],
            values["round"],
            values["team_id"],
        )

        existing = session.get(
            StandingsSnapshot,
            identity,
        )

        if existing is None:

            session.add(
                StandingsSnapshot(
                    **values
                )
            )

            result[
                "inserted"
            ] += 1

            continue

        update_values = {
            key: value
            for key, value in values.items()
            if key not in {
                "season",
                "round",
                "team_id",
            }
        }

        changed = update_model_fields(
            existing,
            update_values,
        )

        if changed:

            result[
                "updated"
            ] += 1

        else:

            result[
                "unchanged"
            ] += 1

    session.flush()

    return result


# =============================================================================
# Contagem
# =============================================================================


def count_rows(
    session: Session,
    model: type,
) -> int:
    """Conta registros de uma tabela."""

    statement = select(
        func.count()
    ).select_from(
        model
    )

    return int(
        session.scalar(
            statement
        )
        or 0
    )


def get_database_counts(
    session: Session,
) -> dict[str, int]:
    """Retorna a quantidade atual de registros."""

    return {
        "teams": count_rows(
            session,
            Team,
        ),
        "matches": count_rows(
            session,
            Match,
        ),
        "standings_snapshots": count_rows(
            session,
            StandingsSnapshot,
        ),
    }


# =============================================================================
# Sincronização completa
# =============================================================================


def sync_database(
    session: Session,
    matches: pd.DataFrame,
) -> dict[str, Any]:
    """
    Sincroniza todo o dataset com o banco.

    Ordem:

    1. times
    2. partidas
    3. snapshots
    """

    infer_season(
        matches
    )

    teams_result = sync_teams(
        session,
        matches,
    )

    matches_result = sync_matches(
        session,
        matches,
    )

    snapshots_result = (
        sync_standings_snapshots(
            session,
            matches,
        )
    )

    counts = get_database_counts(
        session
    )

    return {
        "teams": teams_result,
        "matches": matches_result,
        "standings_snapshots": (
            snapshots_result
        ),
        "counts": counts,
    }


# =============================================================================
# Terminal
# =============================================================================


def print_sync_result(
    label: str,
    result: dict[str, int],
) -> None:
    """Exibe resultado de uma entidade."""

    print(
        f"{label:<24} "
        f"novos={result['inserted']:<4} "
        f"atualizados={result['updated']:<4} "
        f"inalterados={result['unchanged']:<4}"
    )


def main() -> None:
    """Sincroniza os CSVs processados com o SQLite."""

    print()
    print("⚽ Brasileirão Data Lab")
    print("🗄️ V0.3 - Sincronização do Database")
    print("=" * 76)

    print()
    print(
        "[INFO] Carregando partidas..."
    )

    matches = load_matches()

    season = infer_season(
        matches
    )

    print(
        f"[INFO] Temporada detectada: "
        f"{season}"
    )

    print(
        f"[INFO] Partidas disponíveis: "
        f"{len(matches)}"
    )

    print()
    print(
        "[INFO] Inicializando estrutura..."
    )

    init_database(
        engine
    )

    with SessionLocal() as session:

        try:

            result = sync_database(
                session,
                matches,
            )

            session.commit()

        except Exception:

            session.rollback()

            raise

    print()
    print("SINCRONIZAÇÃO")
    print("-" * 76)

    print_sync_result(
        "Times",
        result["teams"],
    )

    print_sync_result(
        "Partidas",
        result["matches"],
    )

    print_sync_result(
        "Snapshots",
        result[
            "standings_snapshots"
        ],
    )

    counts = result[
        "counts"
    ]

    print()
    print("BANCO")
    print("-" * 76)

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

    print()
    print(
        "[SUCCESS] Banco sincronizado."
    )

    print()
    print("=" * 76)


if __name__ == "__main__":
    main()