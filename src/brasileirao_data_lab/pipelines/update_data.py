from __future__ import annotations

from typing import Any

from brasileirao_data_lab.scrapers.cbf import (
    TOTAL_ROUNDS,
    create_session,
    fetch_all_matches,
    fetch_cbf_page,
    parse_standings,
    resolve_next_opponents,
    save_matches_csv,
    save_raw_html,
    save_standings_csv,
)


EXPECTED_TEAMS = 20
EXPECTED_MATCHES = 380


def validate_standings(
    standings: list[dict[str, Any]],
) -> None:
    """Executa validações básicas da classificação."""

    if len(standings) != EXPECTED_TEAMS:
        raise ValueError(
            f"Esperados {EXPECTED_TEAMS} clubes, "
            f"mas foram encontrados "
            f"{len(standings)}."
        )

    positions = [
        team["position"]
        for team in standings
    ]

    if len(positions) != len(
        set(positions)
    ):
        raise ValueError(
            "Existem posições duplicadas "
            "na classificação."
        )

    team_ids = [
        team["team_id"]
        for team in standings
    ]

    if len(team_ids) != len(
        set(team_ids)
    ):
        raise ValueError(
            "Existem IDs de clubes duplicados."
        )


def validate_matches(
    matches: list[dict[str, Any]],
) -> None:
    """Executa validações básicas dos jogos."""

    if not matches:
        raise ValueError(
            "Nenhuma partida foi encontrada."
        )

    match_ids = [
        match["match_id"]
        for match in matches
    ]

    if len(match_ids) != len(
        set(match_ids)
    ):
        raise ValueError(
            "Existem partidas duplicadas."
        )

    invalid_rounds = [
        match["round"]
        for match in matches
        if not 1 <= match["round"] <= TOTAL_ROUNDS
    ]

    if invalid_rounds:
        raise ValueError(
            "Existem partidas com rodada inválida."
        )

    if len(matches) != EXPECTED_MATCHES:
        print(
            f"[WARNING] Esperados "
            f"{EXPECTED_MATCHES} jogos, "
            f"mas foram encontrados "
            f"{len(matches)}."
        )


def update_data() -> None:
    """Atualiza todos os dados principais do Brasileirão."""

    print()
    print("⚽ Brasileirão Data Lab")
    print("=" * 50)

    session = create_session()

    try:
        print()
        print("[INFO] Acessando a CBF...")

        html = fetch_cbf_page(
            session=session
        )

    finally:
        session.close()

    print(
        f"[SUCCESS] Página coletada: "
        f"{len(html):,} caracteres"
    )

    raw_file = save_raw_html(
        html
    )

    print(
        f"[SUCCESS] HTML bruto salvo em: "
        f"{raw_file}"
    )

    # -------------------------------------------------------------------------
    # Classificação
    # -------------------------------------------------------------------------

    print()
    print(
        "[INFO] Extraindo classificação..."
    )

    standings = parse_standings(
        html
    )

    standings = resolve_next_opponents(
        standings
    )

    validate_standings(
        standings
    )

    standings_file = save_standings_csv(
        standings
    )

    print(
        f"[SUCCESS] "
        f"{len(standings)} clubes encontrados."
    )

    print(
        f"[SUCCESS] Classificação salva em: "
        f"{standings_file}"
    )

    print()
    print("Top 5:")
    print("-" * 50)

    for team in standings[:5]:

        print(
            f"{team['position']:>2}º "
            f"{team['team']:<25} "
            f"{team['points']:>3} pts"
        )

    # -------------------------------------------------------------------------
    # Jogos
    # -------------------------------------------------------------------------

    print()
    print(
        "[INFO] Iniciando coleta "
        "das partidas..."
    )
    print()

    matches = fetch_all_matches()

    validate_matches(
        matches
    )

    matches_file = save_matches_csv(
        matches
    )

    played_matches = sum(
        1
        for match in matches
        if (
            match["home_goals"] is not None
            and match["away_goals"] is not None
        )
    )

    future_matches = (
        len(matches)
        - played_matches
    )

    print()
    print(
        f"[SUCCESS] "
        f"{len(matches)} partidas encontradas."
    )

    print(
        f"[INFO] Partidas com placar: "
        f"{played_matches}"
    )

    print(
        f"[INFO] Partidas sem placar: "
        f"{future_matches}"
    )

    print(
        f"[SUCCESS] Partidas salvas em: "
        f"{matches_file}"
    )

    print()
    print("=" * 50)
    print(
        "[SUCCESS] Atualização concluída."
    )
    print()


if __name__ == "__main__":
    update_data()