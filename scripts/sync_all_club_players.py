from __future__ import annotations

import time
from collections import Counter
from typing import Any

from sqlalchemy import select

from brasileirao_data_lab.database.models import (
    Team,
)
from brasileirao_data_lab.database.player_sync import (
    sync_team_players,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
    session_scope,
)


# =============================================================================
# Configurações
# =============================================================================

DELAY_BETWEEN_TEAMS_SECONDS = 1.0


# =============================================================================
# Clubes
# =============================================================================


def get_all_teams() -> list[dict[str, object]]:
    """
    Retorna todos os clubes cadastrados
    no banco principal.

    A lista é ordenada alfabeticamente
    para deixar o log mais legível.
    """

    with SessionLocal() as session:
        statement = (
            select(
                Team.team_id,
                Team.name,
            )
            .order_by(
                Team.name
            )
        )

        rows = (
            session.execute(
                statement
            )
            .mappings()
            .all()
        )

    return [
        {
            "team_id": int(
                row[
                    "team_id"
                ]
            ),
            "name": str(
                row[
                    "name"
                ]
            ),
        }
        for row in rows
    ]


# =============================================================================
# Contadores
# =============================================================================


def empty_counter() -> dict[str, int]:
    """
    Cria contador padrão
    para inserts, updates
    e registros inalterados.
    """

    return {
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
    }


def add_result(
    total: dict[str, int],
    result: dict[str, int],
) -> None:
    """
    Soma o resultado de um clube
    ao resultado global.
    """

    for key in (
        "inserted",
        "updated",
        "unchanged",
    ):
        total[
            key
        ] += int(
            result.get(
                key,
                0,
            )
        )


def total_counter(
    counter: dict[str, int],
) -> int:
    """
    Soma todos os estados
    de um contador.
    """

    return sum(
        int(
            value
        )
        for value in (
            counter.values()
        )
    )


# =============================================================================
# Classificação dos erros
# =============================================================================


def classify_skip_reason(
    reason: str,
) -> str:
    """
    Classifica motivos de atletas
    ignorados em grupos mais úteis
    para o relatório final.
    """

    normalized = (
        reason
        .casefold()
        .strip()
    )

    if (
        "id não resolvido"
        in normalized
    ):
        return "ID não resolvido"

    if (
        "404"
        in normalized
        or (
            "perfil individual"
            in normalized
            and "não encontrado"
            in normalized
        )
    ):
        return "Perfil 404"

    if (
        "500"
        in normalized
        or "502"
        in normalized
        or "503"
        in normalized
        or "504"
        in normalized
    ):
        return "Erro temporário CBF"

    if (
        "estatísticas"
        in normalized
        or "estatistica"
        in normalized
        or "estatísticas"
        in normalized
    ):
        return "Erro de estatísticas"

    return "Outro"


# =============================================================================
# Formatação
# =============================================================================


def calculate_percentage(
    numerator: int,
    denominator: int,
) -> float:
    """
    Retorna percentual seguro
    evitando divisão por zero.
    """

    if denominator <= 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100
    )


def format_duration(
    seconds: float,
) -> str:
    """
    Converte duração em formato
    amigável para o terminal.
    """

    total_seconds = int(
        round(
            seconds
        )
    )

    minutes, seconds_left = divmod(
        total_seconds,
        60,
    )

    hours, minutes_left = divmod(
        minutes,
        60,
    )

    if hours > 0:
        return (
            f"{hours}h "
            f"{minutes_left:02d}min "
            f"{seconds_left:02d}s"
        )

    if minutes > 0:
        return (
            f"{minutes}min "
            f"{seconds_left:02d}s"
        )

    return (
        f"{seconds_left}s"
    )


# =============================================================================
# Execução principal
# =============================================================================


def main() -> None:
    started_at = (
        time.perf_counter()
    )

    print()
    print(
        "⚽ Brasileirão Data Lab"
    )

    print(
        "👥 V1.0 - Sincronização dos jogadores dos 20 clubes"
    )

    print(
        "=" * 110
    )

    print()

    teams = get_all_teams()

    if not teams:
        raise RuntimeError(
            "Nenhum clube encontrado no banco."
        )

    print(
        f"[INFO] Clubes encontrados: "
        f"{len(teams)}"
    )

    if len(
        teams
    ) != 20:
        print(
            "[WARN] A quantidade de clubes "
            "é diferente de 20."
        )

    print()

    # -------------------------------------------------------------------------
    # Totais globais
    # -------------------------------------------------------------------------

    total_players = (
        empty_counter()
    )

    total_stats = (
        empty_counter()
    )

    total_listed_players = 0
    total_processed_players = 0
    total_skipped_players = 0

    # -------------------------------------------------------------------------
    # Clubes
    # -------------------------------------------------------------------------

    completed_teams: list[
        dict[str, Any]
    ] = []

    partial_teams: list[
        dict[str, Any]
    ] = []

    failures: list[
        dict[str, Any]
    ] = []

    # -------------------------------------------------------------------------
    # Atletas ignorados
    # -------------------------------------------------------------------------

    skipped_players: list[
        dict[str, Any]
    ] = []

    skip_reason_counter: Counter[
        str
    ] = Counter()

    # -------------------------------------------------------------------------
    # Loop dos clubes
    # -------------------------------------------------------------------------

    for index, team in enumerate(
        teams,
        start=1,
    ):
        team_started_at = (
            time.perf_counter()
        )

        team_id = int(
            team[
                "team_id"
            ]
        )

        team_name = str(
            team[
                "name"
            ]
        )

        print()

        print(
            "=" * 110
        )

        print(
            f"[{index:02}/{len(teams):02}] "
            f"{team_name} "
            f"({team_id})"
        )

        print(
            "=" * 110
        )

        print()

        try:
            # Uma transação principal
            # por clube.
            #
            # O player_sync também
            # utiliza savepoints
            # individuais por atleta.
            #
            # Dessa forma:
            #
            # atleta com erro
            #     ->
            # somente aquele atleta
            # é ignorado
            #
            # erro fatal do clube
            #     ->
            # apenas aquele clube
            # sofre rollback

            with session_scope() as session:
                result = (
                    sync_team_players(
                        session=session,
                        team_id=team_id,
                    )
                )

            # -----------------------------------------------------------------
            # Totais de persistência
            # -----------------------------------------------------------------

            add_result(
                total_players,
                result[
                    "players"
                ],
            )

            add_result(
                total_stats,
                result[
                    "stats"
                ],
            )

            # -----------------------------------------------------------------
            # Cobertura
            # -----------------------------------------------------------------

            team_total = int(
                result.get(
                    "total",
                    0,
                )
            )

            team_processed = int(
                result.get(
                    "processed",
                    0,
                )
            )

            team_skipped = int(
                result.get(
                    "skipped",
                    0,
                )
            )

            total_listed_players += (
                team_total
            )

            total_processed_players += (
                team_processed
            )

            total_skipped_players += (
                team_skipped
            )

            # -----------------------------------------------------------------
            # Erros individuais
            # -----------------------------------------------------------------

            team_errors = list(
                result.get(
                    "errors",
                    [],
                )
            )

            for error in team_errors:
                reason = str(
                    error.get(
                        "reason",
                        "Motivo desconhecido",
                    )
                )

                category = (
                    classify_skip_reason(
                        reason
                    )
                )

                skip_reason_counter[
                    category
                ] += 1

                skipped_players.append(
                    {
                        "team_id":
                            team_id,
                        "team":
                            team_name,
                        "player_id":
                            error.get(
                                "player_id"
                            ),
                        "player":
                            error.get(
                                "player"
                            )
                            or "Atleta desconhecido",
                        "reason":
                            reason,
                        "category":
                            category,
                    }
                )

            team_duration = (
                time.perf_counter()
                - team_started_at
            )

            team_coverage = (
                calculate_percentage(
                    numerator=(
                        team_processed
                    ),
                    denominator=(
                        team_total
                    ),
                )
            )

            team_summary = {
                "team_id":
                    team_id,
                "team":
                    team_name,
                "total":
                    team_total,
                "processed":
                    team_processed,
                "skipped":
                    team_skipped,
                "coverage":
                    team_coverage,
                "duration":
                    team_duration,
            }

            if team_skipped == 0:
                completed_teams.append(
                    team_summary
                )

            else:
                partial_teams.append(
                    team_summary
                )

            # -----------------------------------------------------------------
            # Log do clube
            # -----------------------------------------------------------------

            print()

            print(
                f"[SUCCESS] "
                f"{team_name} concluído."
            )

            print(
                "          "
                f"Jogadores: "
                f"novos="
                f"{result['players']['inserted']} "
                f"atualizados="
                f"{result['players']['updated']} "
                f"inalterados="
                f"{result['players']['unchanged']}"
            )

            print(
                "          "
                f"Stats: "
                f"novos="
                f"{result['stats']['inserted']} "
                f"atualizados="
                f"{result['stats']['updated']} "
                f"inalterados="
                f"{result['stats']['unchanged']}"
            )

            print(
                "          "
                f"Cobertura: "
                f"{team_processed}/"
                f"{team_total} "
                f"({team_coverage:.1f}%)"
            )

            print(
                "          "
                f"Ignorados: "
                f"{team_skipped}"
            )

            print(
                "          "
                f"Tempo: "
                f"{format_duration(team_duration)}"
            )

            if team_skipped > 0:
                print(
                    "          "
                    "[WARN] Clube concluído "
                    "com dados parciais."
                )

        except Exception as exc:
            team_duration = (
                time.perf_counter()
                - team_started_at
            )

            failures.append(
                {
                    "team_id":
                        team_id,
                    "team":
                        team_name,
                    "error":
                        str(
                            exc
                        ),
                    "duration":
                        team_duration,
                }
            )

            print()

            print(
                f"[ERROR] "
                f"Falha fatal em "
                f"{team_name}: "
                f"{exc}"
            )

            print(
                "[INFO] O script continuará "
                "com o próximo clube."
            )

        if (
            index
            < len(
                teams
            )
        ):
            time.sleep(
                DELAY_BETWEEN_TEAMS_SECONDS
            )

    # =========================================================================
    # Resumo final
    # =========================================================================

    total_duration = (
        time.perf_counter()
        - started_at
    )

    successful_teams = (
        len(
            completed_teams
        )
        + len(
            partial_teams
        )
    )

    global_coverage = (
        calculate_percentage(
            numerator=(
                total_processed_players
            ),
            denominator=(
                total_listed_players
            ),
        )
    )

    print()

    print(
        "=" * 110
    )

    print(
        "📊 RESUMO DA SINCRONIZAÇÃO"
    )

    print(
        "=" * 110
    )

    print()

    # -------------------------------------------------------------------------
    # Clubes
    # -------------------------------------------------------------------------

    print(
        "CLUBES"
    )

    print(
        f"  Encontrados:               "
        f"{len(teams)}"
    )

    print(
        f"  Processados sem erro fatal:"
        f" {successful_teams}"
    )

    print(
        f"  100% completos:            "
        f"{len(completed_teams)}"
    )

    print(
        f"  Com dados parciais:        "
        f"{len(partial_teams)}"
    )

    print(
        f"  Com erro fatal:            "
        f"{len(failures)}"
    )

    print()

    # -------------------------------------------------------------------------
    # Cobertura
    # -------------------------------------------------------------------------

    print(
        "COBERTURA DOS ELENCOS"
    )

    print(
        f"  Atletas listados pela CBF: "
        f"{total_listed_players}"
    )

    print(
        f"  Processados com sucesso:   "
        f"{total_processed_players}"
    )

    print(
        f"  Ignorados:                 "
        f"{total_skipped_players}"
    )

    print(
        f"  Cobertura:                 "
        f"{global_coverage:.2f}%"
    )

    print()

    # -------------------------------------------------------------------------
    # Jogadores
    # -------------------------------------------------------------------------

    print(
        "JOGADORES NO BANCO"
    )

    print(
        f"  Novos:       "
        f"{total_players['inserted']}"
    )

    print(
        f"  Atualizados: "
        f"{total_players['updated']}"
    )

    print(
        f"  Inalterados: "
        f"{total_players['unchanged']}"
    )

    print(
        f"  Total tratado: "
        f"{total_counter(total_players)}"
    )

    print()

    # -------------------------------------------------------------------------
    # Estatísticas
    # -------------------------------------------------------------------------

    print(
        "ESTATÍSTICAS JOGADOR / CLUBE"
    )

    print(
        f"  Novas:       "
        f"{total_stats['inserted']}"
    )

    print(
        f"  Atualizadas: "
        f"{total_stats['updated']}"
    )

    print(
        f"  Inalteradas: "
        f"{total_stats['unchanged']}"
    )

    print(
        f"  Total tratado: "
        f"{total_counter(total_stats)}"
    )

    # -------------------------------------------------------------------------
    # Motivos dos ignorados
    # -------------------------------------------------------------------------

    if skipped_players:
        print()

        print(
            "ATLETAS IGNORADOS POR MOTIVO"
        )

        ordered_categories = [
            "ID não resolvido",
            "Perfil 404",
            "Erro temporário CBF",
            "Erro de estatísticas",
            "Outro",
        ]

        for category in (
            ordered_categories
        ):
            amount = (
                skip_reason_counter.get(
                    category,
                    0,
                )
            )

            if amount <= 0:
                continue

            print(
                f"  {category:<24} "
                f"{amount}"
            )

    # -------------------------------------------------------------------------
    # Clubes parciais
    # -------------------------------------------------------------------------

    if partial_teams:
        print()

        print(
            "-" * 110
        )

        print(
            "⚠️ CLUBES COM DADOS PARCIAIS"
        )

        print(
            "-" * 110
        )

        for team in (
            partial_teams
        ):
            print(
                f"{team['team']} "
                f"({team['team_id']})"
            )

            print(
                "  "
                f"Processados: "
                f"{team['processed']}/"
                f"{team['total']} "
                f"({team['coverage']:.1f}%)"
            )

            print(
                "  "
                f"Ignorados: "
                f"{team['skipped']}"
            )

    # -------------------------------------------------------------------------
    # Lista dos atletas ignorados
    # -------------------------------------------------------------------------

    if skipped_players:
        print()

        print(
            "-" * 110
        )

        print(
            "👤 ATLETAS NÃO SINCRONIZADOS"
        )

        print(
            "-" * 110
        )

        current_team = None

        for item in (
            skipped_players
        ):
            if (
                item[
                    "team"
                ]
                != current_team
            ):
                current_team = (
                    item[
                        "team"
                    ]
                )

                print()

                print(
                    f"{current_team} "
                    f"({item['team_id']})"
                )

            player_id = (
                item[
                    "player_id"
                ]
            )

            player_id_text = (
                str(
                    player_id
                )
                if player_id
                is not None
                else "sem ID"
            )

            print(
                "  - "
                f"{item['player']} "
                f"[{player_id_text}]"
            )

            print(
                "    "
                f"{item['category']}: "
                f"{item['reason']}"
            )

    # -------------------------------------------------------------------------
    # Erros fatais
    # -------------------------------------------------------------------------

    if failures:
        print()

        print(
            "-" * 110
        )

        print(
            "❌ CLUBES COM ERRO FATAL"
        )

        print(
            "-" * 110
        )

        for failure in (
            failures
        ):
            print()

            print(
                f"{failure['team']} "
                f"({failure['team_id']})"
            )

            print(
                f"  Erro: "
                f"{failure['error']}"
            )

            print(
                f"  Tempo antes da falha: "
                f"{format_duration(failure['duration'])}"
            )

    # -------------------------------------------------------------------------
    # Tempo
    # -------------------------------------------------------------------------

    print()

    print(
        "-" * 110
    )

    print(
        f"⏱ Tempo total: "
        f"{format_duration(total_duration)}"
    )

    print(
        "-" * 110
    )

    print()

    # -------------------------------------------------------------------------
    # Status final
    # -------------------------------------------------------------------------

    if failures:
        print(
            "[WARN] Sincronização terminou "
            "com erros fatais em alguns clubes."
        )

        print(
            "[INFO] O script pode ser executado "
            "novamente com segurança."
        )

    elif total_skipped_players > 0:
        print(
            "[SUCCESS] Todos os clubes foram "
            "processados."
        )

        print(
            f"[WARN] "
            f"{total_skipped_players} atleta(s) "
            f"não puderam ser sincronizados."
        )

        print(
            f"[INFO] Cobertura final: "
            f"{global_coverage:.2f}%."
        )

    else:
        print(
            "[SUCCESS] Todos os clubes e "
            "todos os atletas foram "
            "sincronizados com sucesso."
        )

    print()


if __name__ == "__main__":
    main()