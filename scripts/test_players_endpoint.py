from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from brasileirao_data_lab.api.player_router import (
    router,
)


CORINTHIANS_TEAM_ID = 20001

CACA_PLAYER_ID = 510110

EXPECTED_PLAYERS = 38


def main() -> None:
    print()
    print(
        "⚽ Brasileirão Data Lab"
    )
    print(
        "🌐 Teste do endpoint de jogadores"
    )
    print(
        "=" * 100
    )
    print()

    app = FastAPI()

    app.include_router(
        router
    )

    client = TestClient(
        app
    )

    response = client.get(
        f"/api/clubs/"
        f"{CORINTHIANS_TEAM_ID}/players"
    )

    print(
        "[INFO] HTTP:",
        response.status_code,
    )

    if response.status_code != 200:
        print(
            "[ERROR] Resposta:"
        )
        print(
            response.text
        )

        raise SystemExit(
            1
        )

    players = response.json()

    print(
        f"[INFO] Jogadores retornados: "
        f"{len(players)}"
    )

    if (
        len(
            players
        )
        != EXPECTED_PLAYERS
    ):
        raise AssertionError(
            "Quantidade inesperada "
            "de jogadores."
        )

    print()
    print(
        "[SUCCESS] Quantidade correta."
    )

    print()
    print(
        "-" * 100
    )

    print(
        "ID      | "
        "JOGADOR              | "
        "IDADE | "
        "J  | G  | CA | CV | "
        "CLUBE ATUAL"
    )

    print(
        "-" * 100
    )

    for player in players:
        name = (
            player[
                "nickname"
            ]
            or player[
                "full_name"
            ]
        )

        age = (
            player[
                "age"
            ]
            if player[
                "age"
            ]
            is not None
            else "-"
        )

        current_club = (
            player[
                "current_club_name"
            ]
            or "-"
        )

        print(
            f"{player['player_id']:>7} | "
            f"{name:<20} | "
            f"{str(age):>5} | "
            f"{player['matches']:>2} | "
            f"{player['goals']:>2} | "
            f"{player['yellow_cards']:>2} | "
            f"{player['red_cards']:>2} | "
            f"{current_club}"
        )

    caca = next(
        (
            player
            for player in players
            if player[
                "player_id"
            ]
            == CACA_PLAYER_ID
        ),
        None,
    )

    print()
    print(
        "=" * 100
    )
    print(
        "TESTE DE TRANSFERÊNCIA"
    )
    print(
        "-" * 100
    )

    if caca is None:
        raise AssertionError(
            "Cacá não foi retornado."
        )

    print(
        "Jogador:",
        caca[
            "nickname"
        ],
    )

    print(
        "Clube das stats:",
        caca[
            "team"
        ],
    )

    print(
        "Clube atual:",
        caca[
            "current_club_name"
        ],
    )

    print(
        "É clube atual:",
        caca[
            "is_current_club"
        ],
    )

    print(
        "Stats:",
        (
            f"{caca['matches']}J / "
            f"{caca['goals']}G / "
            f"{caca['yellow_cards']}CA / "
            f"{caca['red_cards']}CV"
        ),
    )

    assert (
        caca[
            "team_id"
        ]
        == CORINTHIANS_TEAM_ID
    )

    assert (
        caca[
            "current_club_name"
        ]
        == "Vitória"
    )

    assert (
        caca[
            "is_current_club"
        ]
        is False
    )

    assert (
        caca[
            "matches"
        ]
        == 2
    )

    print()
    print(
        "[SUCCESS] Transferência "
        "representada corretamente."
    )

    print()
    print(
        "=" * 100
    )
    print(
        "[SUCCESS] Endpoint de jogadores "
        "validado com sucesso."
    )


if __name__ == "__main__":
    main()