from __future__ import annotations

from pathlib import Path

import pandas as pd

from brasileirao_data_lab.ml.team_identity import (
    canonical_team_key,
    is_known_team_name,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

HISTORY_FILE = (
    PROJECT_ROOT
    / "data"
    / "ml"
    / "matches_history.csv"
)


def load_team_rows() -> pd.DataFrame:
    history = pd.read_csv(
        HISTORY_FILE
    )

    home = history[
        [
            "season",
            "home_team_id",
            "home_team",
        ]
    ].rename(
        columns={
            "home_team_id": "team_id",
            "home_team": "team_name",
        }
    )

    away = history[
        [
            "season",
            "away_team_id",
            "away_team",
        ]
    ].rename(
        columns={
            "away_team_id": "team_id",
            "away_team": "team_name",
        }
    )

    teams = pd.concat(
        [
            home,
            away,
        ],
        ignore_index=True,
    ).drop_duplicates()

    teams[
        "canonical_key"
    ] = teams[
        "team_name"
    ].map(
        canonical_team_key
    )

    teams[
        "reviewed"
    ] = teams[
        "team_name"
    ].map(
        is_known_team_name
    )

    return teams.sort_values(
        by=[
            "canonical_key",
            "season",
            "team_id",
        ]
    ).reset_index(
        drop=True
    )


def main() -> None:
    print(
        "⚽ Brasileirão Data Lab - Auditoria de identidade dos clubes"
    )

    teams = load_team_rows()

    raw_names = int(
        teams[
            "team_name"
        ].nunique()
    )

    raw_ids = int(
        teams[
            "team_id"
        ].nunique()
    )

    canonical_teams = int(
        teams[
            "canonical_key"
        ].nunique()
    )

    print()
    print("=" * 88)
    print("[SUMMARY]")
    print("=" * 88)
    print(
        f"Nomes brutos distintos: {raw_names}"
    )
    print(
        f"IDs CBF distintos: {raw_ids}"
    )
    print(
        f"Clubes canônicos: {canonical_teams}"
    )

    unknown = (
        teams[
            ~teams[
                "reviewed"
            ]
        ][
            "team_name"
        ]
        .drop_duplicates()
        .tolist()
    )

    print()
    if unknown:
        print(
            "[WARN] Nomes ainda não revisados:"
        )

        for name in unknown:
            print(
                f"  - {name}"
            )
    else:
        print(
            "[SUCCESS] Todos os nomes históricos foram revisados."
        )

    print()
    print(
        "Clubes com mais de um nome bruto ou ID histórico:"
    )

    grouped = (
        teams
        .groupby(
            "canonical_key"
        )
        .agg(
            raw_names=(
                "team_name",
                lambda values: sorted(
                    set(values)
                ),
            ),
            ids=(
                "team_id",
                lambda values: sorted(
                    {
                        int(value)
                        for value in values
                    }
                ),
            ),
            seasons=(
                "season",
                lambda values: sorted(
                    {
                        int(value)
                        for value in values
                    }
                ),
            ),
        )
    )

    found = False

    for canonical_key, row in grouped.iterrows():
        if (
            len(
                row[
                    "raw_names"
                ]
            ) > 1
            or len(
                row[
                    "ids"
                ]
            ) > 1
        ):
            found = True

            names = ", ".join(
                row[
                    "raw_names"
                ]
            )

            ids = ", ".join(
                str(value)
                for value in row[
                    "ids"
                ]
            )

            seasons = ", ".join(
                str(value)
                for value in row[
                    "seasons"
                ]
            )

            print()
            print(
                f"  {canonical_key}"
            )
            print(
                f"    nomes: {names}"
            )
            print(
                f"    ids: {ids}"
            )
            print(
                f"    temporadas: {seasons}"
            )

    if not found:
        print(
            "  Nenhuma troca de identidade encontrada."
        )

    print()
    print("=" * 88)
    print(
        "[DONE] Auditoria concluída."
    )
    print("=" * 88)


if __name__ == "__main__":
    main()