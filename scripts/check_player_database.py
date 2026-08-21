from __future__ import annotations

from sqlalchemy import (
    func,
    select,
)

from brasileirao_data_lab.database.models import (
    Player,
    PlayerTeamCompetitionStat,
    Team,
)
from brasileirao_data_lab.database.session import (
    SessionLocal,
)


CORINTHIANS_TEAM_ID = 20001

SEASON = 2026

COMPETITION_ID = 1260611


def main() -> None:
    print()
    print(
        "⚽ Brasileirão Data Lab"
    )
    print(
        "🔎 Validação do banco de jogadores"
    )
    print(
        "=" * 100
    )
    print()

    session = SessionLocal()

    try:
        player_count = session.scalar(
            select(
                func.count()
            )
            .select_from(
                Player
            )
        )

        stats_count = session.scalar(
            select(
                func.count()
            )
            .select_from(
                PlayerTeamCompetitionStat
            )
        )

        print(
            f"[INFO] Players: "
            f"{player_count or 0}"
        )

        print(
            f"[INFO] Player stats: "
            f"{stats_count or 0}"
        )

        statement = (
            select(
                Player.player_id,
                Player.nickname,
                Player.full_name,
                Player.current_club_name,
                PlayerTeamCompetitionStat.matches,
                PlayerTeamCompetitionStat.goals,
                PlayerTeamCompetitionStat.yellow_cards,
                PlayerTeamCompetitionStat.red_cards,
            )
            .join(
                PlayerTeamCompetitionStat,
                Player.player_id
                == PlayerTeamCompetitionStat.player_id,
            )
            .join(
                Team,
                Team.team_id
                == PlayerTeamCompetitionStat.team_id,
            )
            .where(
                PlayerTeamCompetitionStat.season
                == SEASON,
                PlayerTeamCompetitionStat.competition_id
                == COMPETITION_ID,
                PlayerTeamCompetitionStat.team_id
                == CORINTHIANS_TEAM_ID,
            )
            .order_by(
                PlayerTeamCompetitionStat.matches.desc(),
                Player.nickname,
                Player.full_name,
            )
        )

        rows = (
            session.execute(
                statement
            )
            .mappings()
            .all()
        )

        print()
        print(
            f"[SUCCESS] "
            f"{len(rows)} jogadores "
            "do Corinthians encontrados."
        )

        print()
        print(
            "-" * 100
        )

        print(
            "ID      | "
            "JOGADOR              | "
            "J  | G  | CA | CV | "
            "CLUBE ATUAL"
        )

        print(
            "-" * 100
        )

        for row in rows:
            name = (
                row[
                    "nickname"
                ]
                or row[
                    "full_name"
                ]
            )

            current_club = (
                row[
                    "current_club_name"
                ]
                or "-"
            )

            print(
                f"{row['player_id']:>7} | "
                f"{name:<20} | "
                f"{row['matches']:>2} | "
                f"{row['goals']:>2} | "
                f"{row['yellow_cards']:>2} | "
                f"{row['red_cards']:>2} | "
                f"{current_club}"
            )

        print()
        print(
            "=" * 100
        )

        caca_statement = (
            select(
                Player.player_id,
                Player.nickname,
                Player.current_club_name,
                PlayerTeamCompetitionStat.team_id,
                PlayerTeamCompetitionStat.matches,
                PlayerTeamCompetitionStat.goals,
                PlayerTeamCompetitionStat.yellow_cards,
                PlayerTeamCompetitionStat.red_cards,
            )
            .join(
                PlayerTeamCompetitionStat,
                Player.player_id
                == PlayerTeamCompetitionStat.player_id,
            )
            .where(
                Player.player_id
                == 510110,
                PlayerTeamCompetitionStat.season
                == SEASON,
                PlayerTeamCompetitionStat.competition_id
                == COMPETITION_ID,
                PlayerTeamCompetitionStat.team_id
                == CORINTHIANS_TEAM_ID,
            )
        )

        caca = (
            session.execute(
                caca_statement
            )
            .mappings()
            .one_or_none()
        )

        print()
        print(
            "TESTE DE TRANSFERÊNCIA"
        )
        print(
            "-" * 100
        )

        if caca is None:
            print(
                "[ERROR] Cacá não encontrado."
            )

        else:
            print(
                f"Player ID: "
                f"{caca['player_id']}"
            )

            print(
                f"Jogador: "
                f"{caca['nickname']}"
            )

            print(
                f"Clube atual: "
                f"{caca['current_club_name']}"
            )

            print(
                f"Stats team_id: "
                f"{caca['team_id']}"
            )

            print(
                f"Corinthians Série A: "
                f"{caca['matches']}J / "
                f"{caca['goals']}G / "
                f"{caca['yellow_cards']}CA / "
                f"{caca['red_cards']}CV"
            )

        print()
        print(
            "=" * 100
        )

        if (
            len(
                rows
            )
            == 38
            and caca is not None
            and caca[
                "matches"
            ]
            == 2
        ):
            print(
                "[SUCCESS] Banco de jogadores "
                "validado com sucesso."
            )

        else:
            print(
                "[WARN] Resultado diferente "
                "do esperado."
            )

    finally:
        session.close()


if __name__ == "__main__":
    main()