from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any

import requests

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import Session

from brasileirao_data_lab.database.init_db import (
    init_database,
)
from brasileirao_data_lab.database.models import (
    Player,
    PlayerTeamCompetitionStat,
    Team,
)
from brasileirao_data_lab.database.session import (
    session_scope,
)
from brasileirao_data_lab.scrapers.cbf_player_competition import (
    parse_player_competition_stats,
)
from brasileirao_data_lab.scrapers.cbf_players import (
    CBF_CHAMPIONSHIP_ID,
    CBF_SEASON,
    create_session,
    fetch_player_profile_page,
    fetch_resolved_team_players,
    parse_player_profile,
)


PROFILE_DELAY_SECONDS = 0.05


# =============================================================================
# Conversões
# =============================================================================


def parse_birth_date(
    value: str | None,
) -> date | None:
    """
    Converte data da CBF:

    DD/MM/YYYY

    para datetime.date.
    """

    if value is None:
        return None

    text = value.strip()

    if not text:
        return None

    try:
        return datetime.strptime(
            text,
            "%d/%m/%Y",
        ).date()

    except ValueError:
        return None


# =============================================================================
# Resultados
# =============================================================================


def create_sync_result() -> dict[str, int]:
    """
    Cria contador padrão
    de sincronização.
    """

    return {
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
    }


def update_model_fields(
    instance: Any,
    values: dict[str, Any],
) -> bool:
    """
    Atualiza somente campos
    que realmente mudaram.
    """

    changed = False

    for field_name, new_value in (
        values.items()
    ):
        old_value = getattr(
            instance,
            field_name,
        )

        if old_value == new_value:
            continue

        setattr(
            instance,
            field_name,
            new_value,
        )

        changed = True

    return changed


# =============================================================================
# Player
# =============================================================================


def sync_player(
    session: Session,
    player_data: dict[str, Any],
    profile_data: dict[str, Any],
) -> str:
    """
    Insere ou atualiza um jogador.

    Retorna:

    inserted
    updated
    unchanged
    """

    player_id = int(
        player_data[
            "player_id"
        ]
    )

    values = {
        "full_name": (
            player_data[
                "full_name"
            ]
        ),
        "nickname": (
            player_data.get(
                "nickname"
            )
        ),
        "birth_date": (
            parse_birth_date(
                profile_data.get(
                    "birth_date"
                )
            )
        ),
        "profile_url": (
            player_data.get(
                "profile_url"
            )
        ),
        "current_club_id": (
            player_data.get(
                "api_club_id"
            )
        ),
        "current_club_name": (
            player_data.get(
                "api_club_name"
            )
            or profile_data.get(
                "profile_current_club"
            )
            or player_data.get(
                "listed_current_club"
            )
        ),
        "current_club_state": (
            player_data.get(
                "api_club_state"
            )
        ),
        "current_club_badge_url": (
            player_data.get(
                "club_badge_url"
            )
        ),
    }

    existing = session.get(
        Player,
        player_id,
    )

    if existing is None:
        session.add(
            Player(
                player_id=player_id,
                **values,
            )
        )

        session.flush()

        return "inserted"

    changed = update_model_fields(
        existing,
        values,
    )

    session.flush()

    if changed:
        return "updated"

    return "unchanged"


# =============================================================================
# Estatísticas
# =============================================================================


def sync_player_team_stats(
    session: Session,
    player_id: int,
    team_id: int,
    season: int,
    competition_id: int,
    stats: dict[str, Any],
) -> str:
    """
    Sincroniza as estatísticas
    específicas do jogador naquele
    clube e competição.
    """

    identity = (
        season,
        competition_id,
        player_id,
        team_id,
    )

    values = {
        "competition_name": (
            stats[
                "competition"
            ]
        ),
        "category": (
            stats[
                "category"
            ]
        ),
        "matches": int(
            stats[
                "matches"
            ]
        ),
        "goals": int(
            stats[
                "goals"
            ]
        ),
        "yellow_cards": int(
            stats[
                "yellow_cards"
            ]
        ),
        "red_cards": int(
            stats[
                "red_cards"
            ]
        ),
    }

    existing = session.get(
        PlayerTeamCompetitionStat,
        identity,
    )

    if existing is None:
        session.add(
            PlayerTeamCompetitionStat(
                season=season,
                competition_id=(
                    competition_id
                ),
                player_id=player_id,
                team_id=team_id,
                **values,
            )
        )

        session.flush()

        return "inserted"

    changed = update_model_fields(
        existing,
        values,
    )

    session.flush()

    if changed:
        return "updated"

    return "unchanged"


# =============================================================================
# Validações
# =============================================================================


def ensure_team_exists(
    session: Session,
    team_id: int,
) -> Team:
    """
    Confirma que o clube já existe
    no banco principal.
    """

    team = session.get(
        Team,
        team_id,
    )

    if team is None:
        raise ValueError(
            "Clube não encontrado no banco: "
            f"{team_id}. "
            "Sincronize o banco principal "
            "antes dos jogadores."
        )

    return team


# =============================================================================
# Tratamento de erros
# =============================================================================


def get_http_status_code(
    exc: Exception,
) -> int | None:
    """
    Extrai o HTTP status quando
    disponível.
    """

    if isinstance(
        exc,
        requests.HTTPError,
    ):
        response = exc.response

        if response is not None:
            return (
                response.status_code
            )

    cause = exc.__cause__

    if isinstance(
        cause,
        requests.HTTPError,
    ):
        response = cause.response

        if response is not None:
            return (
                response.status_code
            )

    return None


def build_skip_reason(
    exc: Exception,
) -> str:
    """
    Cria mensagem compacta para
    o log do atleta ignorado.
    """

    status_code = (
        get_http_status_code(
            exc
        )
    )

    if status_code == 404:
        return (
            "perfil individual "
            "não encontrado (404)"
        )

    if status_code is not None:
        return (
            f"erro HTTP "
            f"{status_code}: "
            f"{exc}"
        )

    return str(
        exc
    )


# =============================================================================
# Sincronização do clube
# =============================================================================


def sync_team_players(
    session: Session,
    team_id: int,
    season: int = CBF_SEASON,
    competition_id: int = CBF_CHAMPIONSHIP_ID,
    profile_delay: float = PROFILE_DELAY_SECONDS,
) -> dict[str, Any]:
    """
    Sincroniza jogadores e estatísticas
    de um clube.

    Fluxo:

    página do clube
        ->
    API atual de atletas
        ->
    fallback por escalações
        ->
    perfil individual
        ->
    estatísticas Série A + clube
        ->
    SQLite

    Um erro individual não interrompe
    a sincronização do restante
    do elenco.
    """

    team = ensure_team_exists(
        session,
        team_id,
    )

    listed_players = (
        fetch_resolved_team_players(
            team_id=team_id,
            season=season,
            championship_id=(
                competition_id
            ),
        )
    )

    players_result = (
        create_sync_result()
    )

    stats_result = (
        create_sync_result()
    )

    skipped = 0

    errors: list[
        dict[str, Any]
    ] = []

    http = create_session()

    try:
        for index, player in enumerate(
            listed_players,
            start=1,
        ):
            display_name = (
                player.get(
                    "nickname"
                )
                or player.get(
                    "full_name"
                )
                or "Atleta"
            )

            player_id = (
                player.get(
                    "player_id"
                )
            )

            if player_id is None:
                skipped += 1

                reason = (
                    "ID não resolvido "
                    "pela API nem pelas "
                    "escalações"
                )

                errors.append(
                    {
                        "player_id": None,
                        "player": (
                            player.get(
                                "full_name"
                            )
                        ),
                        "reason": reason,
                    }
                )

                print(
                    f"[{index:02}/{len(listed_players)}] "
                    f"{display_name} "
                    f"-> [WARN] ignorado: "
                    f"{reason}"
                )

                continue

            player_id = int(
                player_id
            )

            try:
                html = (
                    fetch_player_profile_page(
                        player_id=player_id,
                        season=season,
                        session=http,
                    )
                )

                profile_data = (
                    parse_player_profile(
                        html=html,
                        player_id=player_id,
                        season=season,
                    )
                )

                stats = (
                    parse_player_competition_stats(
                        html=html,
                        player_id=player_id,
                        season=season,
                        team_id=team_id,
                    )
                )

                # Savepoint individual.
                #
                # Se houver erro ao gravar
                # este jogador, somente
                # suas alterações voltam.
                with session.begin_nested():
                    player_status = (
                        sync_player(
                            session=session,
                            player_data=player,
                            profile_data=(
                                profile_data
                            ),
                        )
                    )

                    stats_status = (
                        sync_player_team_stats(
                            session=session,
                            player_id=player_id,
                            team_id=team_id,
                            season=season,
                            competition_id=(
                                competition_id
                            ),
                            stats=stats,
                        )
                    )

                players_result[
                    player_status
                ] += 1

                stats_result[
                    stats_status
                ] += 1

                resolution_source = (
                    player.get(
                        "resolution_source"
                    )
                    or "unknown"
                )

                source_suffix = (
                    " [escalação]"
                    if resolution_source
                    == "lineups"
                    else ""
                )

                print(
                    f"[{index:02}/{len(listed_players)}] "
                    f"{display_name} "
                    f"-> "
                    f"{stats['matches']}J "
                    f"{stats['goals']}G "
                    f"{stats['yellow_cards']}CA "
                    f"{stats['red_cards']}CV"
                    f"{source_suffix}"
                )

            except Exception as exc:
                skipped += 1

                reason = (
                    build_skip_reason(
                        exc
                    )
                )

                errors.append(
                    {
                        "player_id": (
                            player_id
                        ),
                        "player": (
                            player.get(
                                "full_name"
                            )
                        ),
                        "reason": reason,
                    }
                )

                print(
                    f"[{index:02}/{len(listed_players)}] "
                    f"{display_name} "
                    f"-> [WARN] ignorado: "
                    f"{reason}"
                )

            if (
                profile_delay > 0
                and index
                < len(
                    listed_players
                )
            ):
                time.sleep(
                    profile_delay
                )

    finally:
        http.close()

    processed = (
        players_result[
            "inserted"
        ]
        + players_result[
            "updated"
        ]
        + players_result[
            "unchanged"
        ]
    )

    return {
        "team_id": team.team_id,
        "team": team.name,
        "season": season,
        "competition_id": (
            competition_id
        ),
        "players": players_result,
        "stats": stats_result,
        "total": len(
            listed_players
        ),
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
    }


# =============================================================================
# Contagens
# =============================================================================


def count_players(
    session: Session,
) -> int:
    """
    Conta jogadores armazenados.
    """

    statement = (
        select(
            func.count()
        )
        .select_from(
            Player
        )
    )

    return int(
        session.scalar(
            statement
        )
        or 0
    )


def count_player_stats(
    session: Session,
) -> int:
    """
    Conta registros de estatísticas
    jogador/clube/competição.
    """

    statement = (
        select(
            func.count()
        )
        .select_from(
            PlayerTeamCompetitionStat
        )
    )

    return int(
        session.scalar(
            statement
        )
        or 0
    )


# =============================================================================
# Terminal
# =============================================================================


def print_result(
    label: str,
    result: dict[str, int],
) -> None:
    """
    Exibe resultado de sincronização.
    """

    print(
        f"{label:<16} "
        f"novos={result['inserted']:<4} "
        f"atualizados={result['updated']:<4} "
        f"inalterados={result['unchanged']:<4}"
    )


def main() -> None:
    """
    Sincroniza inicialmente
    os atletas do Corinthians.
    """

    team_id = 20001

    print()
    print(
        "⚽ Brasileirão Data Lab"
    )
    print(
        "🧑‍💻 V1.0 - Player Database"
    )
    print(
        "=" * 80
    )
    print()

    print(
        "[INFO] Inicializando tabelas..."
    )

    tables = init_database()

    print(
        "[SUCCESS] Tabelas disponíveis:",
        len(
            tables
        ),
    )

    print()
    print(
        "[INFO] Sincronizando jogadores "
        "do Corinthians..."
    )
    print()

    with session_scope() as session:
        result = sync_team_players(
            session=session,
            team_id=team_id,
        )

        total_players = count_players(
            session
        )

        total_stats = (
            count_player_stats(
                session
            )
        )

    print()
    print(
        "=" * 80
    )

    print(
        f"Clube: "
        f"{result['team']} "
        f"({result['team_id']})"
    )

    print(
        f"Temporada: "
        f"{result['season']}"
    )

    print(
        f"Competition ID: "
        f"{result['competition_id']}"
    )

    print()

    print_result(
        "Jogadores:",
        result[
            "players"
        ],
    )

    print_result(
        "Estatísticas:",
        result[
            "stats"
        ],
    )

    print()

    print(
        f"Processados: "
        f"{result['processed']}/"
        f"{result['total']}"
    )

    print(
        f"Ignorados: "
        f"{result['skipped']}"
    )

    if result[
        "errors"
    ]:
        print()

        print(
            "Atletas ignorados:"
        )

        for error in (
            result[
                "errors"
            ]
        ):
            print(
                "  - "
                f"{error['player']}: "
                f"{error['reason']}"
            )

    print()

    print(
        f"Players no banco: "
        f"{total_players}"
    )

    print(
        f"Stats no banco: "
        f"{total_stats}"
    )

    print()
    print(
        "=" * 80
    )

    print(
        "[SUCCESS] Sincronização concluída."
    )


if __name__ == "__main__":
    main()