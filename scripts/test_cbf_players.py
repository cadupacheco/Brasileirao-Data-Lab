from __future__ import annotations

from brasileirao_data_lab.scrapers.cbf_players import (
    fetch_team_players_with_stats,
)


CORINTHIANS_TEAM_ID = 20001


def format_value(
    value: object,
) -> str:
    if value is None:
        return "-"

    return str(
        value
    )


def main() -> None:
    print()
    print(
        "⚽ Brasileirão Data Lab"
    )
    print(
        "🧑‍💻 Teste completo de atletas da CBF"
    )
    print(
        "=" * 100
    )
    print()

    print(
        "[INFO] Coletando atletas, IDs "
        "e estatísticas do Corinthians..."
    )

    players = (
        fetch_team_players_with_stats(
            team_id=(
                CORINTHIANS_TEAM_ID
            ),
        )
    )

    resolved = [
        player
        for player in players
        if player[
            "player_id"
        ] is not None
    ]

    unresolved = [
        player
        for player in players
        if player[
            "player_id"
        ] is None
    ]

    with_stats = [
        player
        for player in players
        if player[
            "matches"
        ] is not None
    ]

    print()
    print(
        f"[SUCCESS] "
        f"{len(players)} atletas "
        "listados pelo clube."
    )

    print(
        f"[SUCCESS] "
        f"{len(resolved)} atletas "
        "com ID resolvido."
    )

    print(
        f"[SUCCESS] "
        f"{len(with_stats)} atletas "
        "com estatísticas."
    )

    print()

    print(
        "-" * 100
    )

    print(
        "ID      | "
        "APELIDO              | "
        "CLUBE API       | "
        "J  | G  | CA | CV | "
        "IDADE"
    )

    print(
        "-" * 100
    )

    for player in players:
        print(
            f"{format_value(player['player_id']):>7} | "
            f"{format_value(player['nickname']):<20} | "
            f"{format_value(player['api_club_name']):<15} | "
            f"{format_value(player['matches']):>2} | "
            f"{format_value(player['goals']):>2} | "
            f"{format_value(player['yellow_cards']):>2} | "
            f"{format_value(player['red_cards']):>2} | "
            f"{format_value(player['age']):>5}"
        )

    print()
    print(
        "-" * 100
    )

    print(
        f"[INFO] Não resolvidos: "
        f"{len(unresolved)}"
    )

    for player in unresolved:
        print(
            "  "
            f"{player['nickname']} | "
            f"{player['full_name']}"
        )

    print()
    print(
        "=" * 100
    )

    print(
        "[SUCCESS] Teste concluído."
    )


if __name__ == "__main__":
    main()