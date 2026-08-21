from __future__ import annotations

from brasileirao_data_lab.scrapers.cbf_player_competition import (
    create_competition_session,
    fetch_player_competition_stats,
)
from brasileirao_data_lab.scrapers.cbf_players import (
    fetch_resolved_team_players,
)


CORINTHIANS_TEAM_ID = 20001


def main() -> None:
    print()
    print(
        "⚽ Brasileirão Data Lab"
    )
    print(
        "🏟️ Auditoria de jogadores "
        "por clube"
    )
    print(
        "=" * 110
    )
    print()

    players = (
        fetch_resolved_team_players(
            team_id=(
                CORINTHIANS_TEAM_ID
            )
        )
    )

    print(
        f"[SUCCESS] "
        f"{len(players)} atletas "
        "resolvidos."
    )

    print()

    session = (
        create_competition_session()
    )

    results = []

    try:
        for index, player in enumerate(
            players,
            start=1,
        ):
            player_id = (
                player[
                    "player_id"
                ]
            )

            stats = (
                fetch_player_competition_stats(
                    player_id=player_id,
                    team_id=(
                        CORINTHIANS_TEAM_ID
                    ),
                    session=session,
                )
            )

            result = {
                **player,
                **stats,
            }

            results.append(
                result
            )

            print(
                f"[{index:02}/{len(players)}] "
                f"{player['nickname'] or player['full_name']} "
                f"-> Corinthians "
                f"{stats['matches']}J/"
                f"{stats['goals']}G | "
                f"Série A total "
                f"{stats['competition_matches']}J/"
                f"{stats['competition_goals']}G"
            )

    finally:
        session.close()

    print()
    print(
        "=" * 110
    )
    print(
        "RESULTADO"
    )
    print(
        "=" * 110
    )

    different_club_totals = []

    for player in results:
        differs = (
            player[
                "matches"
            ]
            != player[
                "competition_matches"
            ]
            or player[
                "goals"
            ]
            != player[
                "competition_goals"
            ]
            or player[
                "yellow_cards"
            ]
            != player[
                "competition_yellow_cards"
            ]
            or player[
                "red_cards"
            ]
            != player[
                "competition_red_cards"
            ]
        )

        if differs:
            different_club_totals.append(
                player
            )

    print()
    print(
        f"[INFO] Jogadores analisados: "
        f"{len(results)}"
    )

    print(
        f"[INFO] Estatísticas da Série A "
        f"iguais às do Corinthians: "
        f"{len(results) - len(different_club_totals)}"
    )

    print(
        f"[INFO] Jogadores com jogos "
        f"da Série A por outro clube: "
        f"{len(different_club_totals)}"
    )

    if different_club_totals:
        print()
        print(
            "[INFO] Casos que exigem "
            "separação por clube:"
        )

        for player in (
            different_club_totals
        ):
            print(
                "  "
                f"{player['nickname'] or player['full_name']} | "
                f"Corinthians: "
                f"{player['matches']}J/"
                f"{player['goals']}G/"
                f"{player['yellow_cards']}CA/"
                f"{player['red_cards']}CV | "
                f"Série A total: "
                f"{player['competition_matches']}J/"
                f"{player['competition_goals']}G/"
                f"{player['competition_yellow_cards']}CA/"
                f"{player['competition_red_cards']}CV | "
                f"Clube atual: "
                f"{player['api_club_name']}"
            )

    print()
    print(
        "=" * 110
    )
    print(
        "[SUCCESS] Auditoria concluída."
    )


if __name__ == "__main__":
    main()