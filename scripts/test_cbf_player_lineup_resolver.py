from __future__ import annotations

from brasileirao_data_lab.scrapers.cbf_player_lineups import (
    build_championship_lineup_resolver,
    resolve_player_from_lineups,
)


TEST_PLAYERS = [
    {
        "full_name":
            "Raul Lô Gonçalves",
        "team_id":
            20052,
        "team":
            "Athletico Paranaense",
        "expected_id":
            446399,
    },
    {
        "full_name":
            "Raphael Cavalcante Veiga",
        "team_id":
            20002,
        "team":
            "Palmeiras",
        "expected_id":
            308405,
    },
    {
        "full_name":
            "Julio Cesar de Rezende Miranda",
        "team_id":
            61377,
        "team":
            "Bahia",
        "expected_id":
            None,
    },
    {
        "full_name":
            "Joao Othavio Basso",
        "team_id":
            20008,
        "team":
            "Santos FC",
        "expected_id":
            294407,
    },
]


def main() -> None:
    print()
    print(
        "⚽ Brasileirão Data Lab"
    )
    print(
        "🧩 Resolver de atletas "
        "por escalações"
    )
    print(
        "=" * 100
    )

    print()
    print(
        "[INFO] Construindo índice "
        "das escalações da Série A..."
    )

    indexes, metadata = (
        build_championship_lineup_resolver()
    )

    print()
    print(
        "=" * 100
    )
    print(
        "RESUMO DO ÍNDICE"
    )
    print(
        "=" * 100
    )

    print(
        f"Registros de escalação: "
        f"{metadata['lineup_records']}"
    )

    print(
        f"Atletas únicos: "
        f"{metadata['unique_players']}"
    )

    failed_rounds = (
        metadata[
            "failed_rounds"
        ]
    )

    if failed_rounds:
        print(
            "[WARN] Rodadas com "
            "falha definitiva: "
            + ", ".join(
                str(
                    round_number
                )
                for round_number
                in failed_rounds
            )
        )
    else:
        print(
            "[SUCCESS] Todas as "
            "rodadas responderam."
        )

    print()
    print(
        "=" * 100
    )
    print(
        "TESTES DE RESOLUÇÃO"
    )
    print(
        "=" * 100
    )

    resolved_count = 0

    expected_matches = 0

    unexpected_results = 0

    for player in TEST_PLAYERS:
        print()
        print(
            "-" * 100
        )

        print(
            f"Jogador: "
            f"{player['full_name']}"
        )

        print(
            f"Clube: "
            f"{player['team']} "
            f"({player['team_id']})"
        )

        result = (
            resolve_player_from_lineups(
                indexes=indexes,
                full_name=(
                    player[
                        "full_name"
                    ]
                ),
                team_id=int(
                    player[
                        "team_id"
                    ]
                ),
            )
        )

        if result is None:
            print(
                "[WARN] Não encontrado "
                "nas escalações coletadas."
            )

            if (
                player[
                    "expected_id"
                ]
                is None
            ):
                print(
                    "[INFO] Resultado "
                    "aceitável para este "
                    "diagnóstico."
                )

            else:
                unexpected_results += 1

            continue

        resolved_count += 1

        player_id = int(
            result[
                "player_id"
            ]
        )

        print(
            f"[SUCCESS] ID resolvido: "
            f"{player_id}"
        )

        print(
            f"[INFO] Nome da escalação: "
            f"{result['full_name']}"
        )

        print(
            f"[INFO] Apelido: "
            f"{result.get('nickname')}"
        )

        print(
            f"[INFO] Clube da escalação: "
            f"{result['team_name']} "
            f"({result['team_id']})"
        )

        print(
            f"[INFO] Encontrado na "
            f"rodada: "
            f"{result['round']}"
        )

        print(
            f"[INFO] Jogo ID: "
            f"{result['match_id']}"
        )

        expected_id = (
            player[
                "expected_id"
            ]
        )

        if expected_id is None:
            print(
                "[INFO] Não havia ID "
                "esperado pré-definido."
            )

            continue

        if (
            player_id
            == int(
                expected_id
            )
        ):
            expected_matches += 1

            print(
                "[SUCCESS] ID confere "
                "com a evidência já "
                "coletada."
            )

        else:
            unexpected_results += 1

            print(
                "[ERROR] ID diferente "
                "do esperado."
            )

            print(
                f"Esperado: "
                f"{expected_id}"
            )

            print(
                f"Obtido: "
                f"{player_id}"
            )

    print()
    print(
        "=" * 100
    )
    print(
        "RESULTADO"
    )
    print(
        "=" * 100
    )

    print(
        f"Jogadores resolvidos: "
        f"{resolved_count}/"
        f"{len(TEST_PLAYERS)}"
    )

    print(
        f"IDs conhecidos conferidos: "
        f"{expected_matches}/3"
    )

    if unexpected_results == 0:
        print()
        print(
            "[SUCCESS] Resolver de "
            "escalações validado."
        )

        print(
            "[NEXT] Podemos integrar "
            "este fallback ao coletor "
            "principal de jogadores."
        )

    else:
        print()
        print(
            f"[WARN] Foram encontrados "
            f"{unexpected_results} "
            f"resultados inesperados."
        )


if __name__ == "__main__":
    main()