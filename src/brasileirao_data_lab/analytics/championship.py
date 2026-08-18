from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a pasta raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_matches_file() -> Path:
    """Retorna o caminho padrão do arquivo de partidas."""

    return (
        get_project_root()
        / "data"
        / "processed"
        / "matches.csv"
    )


def get_standings_file() -> Path:
    """Retorna o caminho padrão da classificação oficial."""

    return (
        get_project_root()
        / "data"
        / "processed"
        / "standings.csv"
    )


# =============================================================================
# Carregamento
# =============================================================================


def load_matches(
    file_path: Path | str | None = None,
) -> pd.DataFrame:
    """
    Carrega o dataset de partidas do Brasileirão.

    Se nenhum caminho for informado, utiliza:
    data/processed/matches.csv
    """

    path = (
        Path(file_path)
        if file_path is not None
        else get_matches_file()
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo de partidas não encontrado: {path}"
        )

    return pd.read_csv(path)


def load_standings(
    file_path: Path | str | None = None,
) -> pd.DataFrame:
    """
    Carrega a classificação oficial coletada da CBF.

    Se nenhum caminho for informado, utiliza:
    data/processed/standings.csv
    """

    path = (
        Path(file_path)
        if file_path is not None
        else get_standings_file()
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo de classificação não encontrado: {path}"
        )

    return pd.read_csv(path)


def load_matches_by_source(
    source: str = "csv",
) -> pd.DataFrame:
    """
    Carrega partidas a partir da fonte solicitada.

    Fontes disponíveis:

    csv
        data/processed/matches.csv

    database
        SQLite através da camada Database.
    """

    normalized_source = (
        source.strip()
        .lower()
    )

    if normalized_source == "csv":

        return load_matches()

    if normalized_source == "database":

        # Imports locais evitam dependência circular,
        # pois analytics_bridge também utiliza funções
        # deste módulo.
        from brasileirao_data_lab.database.analytics_bridge import (
            load_matches_for_analytics,
        )
        from brasileirao_data_lab.database.session import (
            SessionLocal,
        )

        with SessionLocal() as session:

            return load_matches_for_analytics(
                session
            )

    raise ValueError(
        "Fonte inválida. "
        "Utilize 'csv' ou 'database'."
    )


# =============================================================================
# Jogos realizados e futuros
# =============================================================================


def get_played_matches(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna somente partidas que possuem placar."""

    mask = (
        matches["home_goals"].notna()
        & matches["away_goals"].notna()
    )

    return matches.loc[
        mask
    ].copy()


def get_future_matches(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna partidas que ainda não possuem placar."""

    mask = (
        matches["home_goals"].isna()
        | matches["away_goals"].isna()
    )

    return matches.loc[
        mask
    ].copy()


# =============================================================================
# Resultado da partida
# =============================================================================


def add_match_result(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Adiciona a coluna result.

    H = vitória do mandante
    D = empate
    A = vitória do visitante
    """

    dataframe = matches.copy()

    dataframe["result"] = None

    home_win = (
        dataframe["home_goals"]
        > dataframe["away_goals"]
    )

    draw = (
        dataframe["home_goals"]
        == dataframe["away_goals"]
    )

    away_win = (
        dataframe["home_goals"]
        < dataframe["away_goals"]
    )

    dataframe.loc[
        home_win,
        "result",
    ] = "H"

    dataframe.loc[
        draw,
        "result",
    ] = "D"

    dataframe.loc[
        away_win,
        "result",
    ] = "A"

    return dataframe


# =============================================================================
# Ordenação cronológica
# =============================================================================


def sort_matches_chronologically(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Ordena partidas pela data e horário.

    Rodada e número da partida são utilizados como
    critérios auxiliares de ordenação.
    """

    dataframe = matches.copy()

    date_values = (
        dataframe["date"].fillna("")
        if "date" in dataframe.columns
        else pd.Series(
            "",
            index=dataframe.index,
        )
    )

    time_values = (
        dataframe["time"].fillna(
            "00:00"
        )
        if "time" in dataframe.columns
        else pd.Series(
            "00:00",
            index=dataframe.index,
        )
    )

    dataframe["_kickoff"] = pd.to_datetime(
        date_values.astype(
            str
        )
        + " "
        + time_values.astype(
            str
        ),
        errors="coerce",
    )

    sort_columns = [
        "_kickoff",
    ]

    if "round" in dataframe.columns:

        sort_columns.append(
            "round"
        )

    if "match_number" in dataframe.columns:

        sort_columns.append(
            "match_number"
        )

    dataframe = dataframe.sort_values(
        by=sort_columns,
        na_position="last",
    )

    return dataframe.drop(
        columns=[
            "_kickoff"
        ]
    )


# =============================================================================
# Estatísticas gerais
# =============================================================================


def get_championship_summary(
    matches: pd.DataFrame,
) -> dict:
    """Calcula estatísticas gerais do campeonato."""

    played = get_played_matches(
        matches
    )

    future = get_future_matches(
        matches
    )

    played = add_match_result(
        played
    )

    total_matches = len(
        matches
    )

    played_matches = len(
        played
    )

    future_matches = len(
        future
    )

    total_goals = int(
        played["home_goals"].sum()
        + played["away_goals"].sum()
    )

    home_goals = int(
        played["home_goals"].sum()
    )

    away_goals = int(
        played["away_goals"].sum()
    )

    home_wins = int(
        (
            played["result"]
            == "H"
        ).sum()
    )

    draws = int(
        (
            played["result"]
            == "D"
        ).sum()
    )

    away_wins = int(
        (
            played["result"]
            == "A"
        ).sum()
    )

    average_goals = (
        total_goals
        / played_matches
        if played_matches
        else 0
    )

    return {
        "total_matches": total_matches,
        "played_matches": played_matches,
        "future_matches": future_matches,
        "total_goals": total_goals,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "average_goals_per_match": round(
            average_goals,
            2,
        ),
        "home_wins": home_wins,
        "draws": draws,
        "away_wins": away_wins,
    }


# =============================================================================
# Clubes encontrados nos jogos
# =============================================================================


def get_teams(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna a lista única de clubes presentes nos jogos."""

    home_teams = (
        matches[
            [
                "home_team_id",
                "home_team",
            ]
        ]
        .rename(
            columns={
                "home_team_id": "team_id",
                "home_team": "team",
            }
        )
    )

    away_teams = (
        matches[
            [
                "away_team_id",
                "away_team",
            ]
        ]
        .rename(
            columns={
                "away_team_id": "team_id",
                "away_team": "team",
            }
        )
    )

    return (
        pd.concat(
            [
                home_teams,
                away_teams,
            ],
            ignore_index=True,
        )
        .dropna(
            subset=[
                "team_id"
            ]
        )
        .drop_duplicates(
            subset=[
                "team_id"
            ]
        )
        .sort_values(
            "team_id"
        )
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Casa x fora
# =============================================================================


def get_home_away_stats(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula as estatísticas de cada clube separando
    partidas como mandante e visitante.
    """

    played = get_played_matches(
        matches
    )

    if played.empty:

        return pd.DataFrame()

    teams = get_teams(
        played
    )

    stats = []

    for _, team_row in teams.iterrows():

        team_id = int(
            team_row[
                "team_id"
            ]
        )

        team_name = team_row[
            "team"
        ]

        home = played[
            played[
                "home_team_id"
            ]
            == team_id
        ]

        away = played[
            played[
                "away_team_id"
            ]
            == team_id
        ]

        # ---------------------------------------------------------------------
        # Casa
        # ---------------------------------------------------------------------

        home_matches = len(
            home
        )

        home_wins = int(
            (
                home[
                    "home_goals"
                ]
                > home[
                    "away_goals"
                ]
            ).sum()
        )

        home_draws = int(
            (
                home[
                    "home_goals"
                ]
                == home[
                    "away_goals"
                ]
            ).sum()
        )

        home_losses = (
            home_matches
            - home_wins
            - home_draws
        )

        home_goals_for = int(
            home[
                "home_goals"
            ].sum()
        )

        home_goals_against = int(
            home[
                "away_goals"
            ].sum()
        )

        home_goal_difference = (
            home_goals_for
            - home_goals_against
        )

        home_points = (
            home_wins * 3
            + home_draws
        )

        home_performance = (
            (
                home_points
                / (
                    home_matches
                    * 3
                )
                * 100
            )
            if home_matches
            else 0
        )

        # ---------------------------------------------------------------------
        # Fora
        # ---------------------------------------------------------------------

        away_matches = len(
            away
        )

        away_wins = int(
            (
                away[
                    "away_goals"
                ]
                > away[
                    "home_goals"
                ]
            ).sum()
        )

        away_draws = int(
            (
                away[
                    "away_goals"
                ]
                == away[
                    "home_goals"
                ]
            ).sum()
        )

        away_losses = (
            away_matches
            - away_wins
            - away_draws
        )

        away_goals_for = int(
            away[
                "away_goals"
            ].sum()
        )

        away_goals_against = int(
            away[
                "home_goals"
            ].sum()
        )

        away_goal_difference = (
            away_goals_for
            - away_goals_against
        )

        away_points = (
            away_wins * 3
            + away_draws
        )

        away_performance = (
            (
                away_points
                / (
                    away_matches
                    * 3
                )
                * 100
            )
            if away_matches
            else 0
        )

        stats.append(
            {
                "team_id": team_id,
                "team": team_name,

                "home_matches": home_matches,
                "home_wins": home_wins,
                "home_draws": home_draws,
                "home_losses": home_losses,
                "home_goals_for": home_goals_for,
                "home_goals_against": home_goals_against,
                "home_goal_difference": home_goal_difference,
                "home_points": home_points,
                "home_performance_pct": round(
                    home_performance,
                    2,
                ),

                "away_matches": away_matches,
                "away_wins": away_wins,
                "away_draws": away_draws,
                "away_losses": away_losses,
                "away_goals_for": away_goals_for,
                "away_goals_against": away_goals_against,
                "away_goal_difference": away_goal_difference,
                "away_points": away_points,
                "away_performance_pct": round(
                    away_performance,
                    2,
                ),
            }
        )

    return (
        pd.DataFrame(
            stats
        )
        .sort_values(
            "team"
        )
        .reset_index(
            drop=True
        )
    )


def get_home_ranking(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna o ranking dos melhores mandantes."""

    stats = get_home_away_stats(
        matches
    )

    if stats.empty:

        return stats

    ranking = stats.sort_values(
        by=[
            "home_points",
            "home_wins",
            "home_goal_difference",
            "home_goals_for",
        ],
        ascending=[
            False,
            False,
            False,
            False,
        ],
    ).reset_index(
        drop=True
    )

    ranking.insert(
        0,
        "home_position",
        range(
            1,
            len(ranking) + 1,
        ),
    )

    return ranking


def get_away_ranking(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna o ranking dos melhores visitantes."""

    stats = get_home_away_stats(
        matches
    )

    if stats.empty:

        return stats

    ranking = stats.sort_values(
        by=[
            "away_points",
            "away_wins",
            "away_goal_difference",
            "away_goals_for",
        ],
        ascending=[
            False,
            False,
            False,
            False,
        ],
    ).reset_index(
        drop=True
    )

    ranking.insert(
        0,
        "away_position",
        range(
            1,
            len(ranking) + 1,
        ),
    )

    return ranking


# =============================================================================
# Estatísticas gerais por clube
# =============================================================================


def get_team_stats(
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Reconstrói a classificação utilizando somente
    as partidas já realizadas.
    """

    venue_stats = get_home_away_stats(
        matches
    )

    if venue_stats.empty:

        return pd.DataFrame()

    stats = []

    for _, team in venue_stats.iterrows():

        matches_played = int(
            team[
                "home_matches"
            ]
            + team[
                "away_matches"
            ]
        )

        wins = int(
            team[
                "home_wins"
            ]
            + team[
                "away_wins"
            ]
        )

        draws = int(
            team[
                "home_draws"
            ]
            + team[
                "away_draws"
            ]
        )

        losses = int(
            team[
                "home_losses"
            ]
            + team[
                "away_losses"
            ]
        )

        goals_for = int(
            team[
                "home_goals_for"
            ]
            + team[
                "away_goals_for"
            ]
        )

        goals_against = int(
            team[
                "home_goals_against"
            ]
            + team[
                "away_goals_against"
            ]
        )

        goal_difference = (
            goals_for
            - goals_against
        )

        points = (
            wins * 3
            + draws
        )

        performance = (
            (
                points
                / (
                    matches_played
                    * 3
                )
                * 100
            )
            if matches_played
            else 0
        )

        stats.append(
            {
                "team_id": int(
                    team[
                        "team_id"
                    ]
                ),
                "team": team[
                    "team"
                ],
                "matches": matches_played,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "goal_difference": goal_difference,
                "points": points,
                "performance_pct": round(
                    performance,
                    2,
                ),

                "home_matches": int(
                    team[
                        "home_matches"
                    ]
                ),
                "home_wins": int(
                    team[
                        "home_wins"
                    ]
                ),
                "home_draws": int(
                    team[
                        "home_draws"
                    ]
                ),
                "home_losses": int(
                    team[
                        "home_losses"
                    ]
                ),
                "home_points": int(
                    team[
                        "home_points"
                    ]
                ),
                "home_performance_pct": float(
                    team[
                        "home_performance_pct"
                    ]
                ),

                "away_matches": int(
                    team[
                        "away_matches"
                    ]
                ),
                "away_wins": int(
                    team[
                        "away_wins"
                    ]
                ),
                "away_draws": int(
                    team[
                        "away_draws"
                    ]
                ),
                "away_losses": int(
                    team[
                        "away_losses"
                    ]
                ),
                "away_points": int(
                    team[
                        "away_points"
                    ]
                ),
                "away_performance_pct": float(
                    team[
                        "away_performance_pct"
                    ]
                ),
            }
        )

    dataframe = pd.DataFrame(
        stats
    )

    dataframe = (
        dataframe.sort_values(
            by=[
                "points",
                "wins",
                "goal_difference",
                "goals_for",
            ],
            ascending=[
                False,
                False,
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    dataframe.insert(
        0,
        "calculated_position",
        range(
            1,
            len(dataframe) + 1,
        ),
    )

    return dataframe


# =============================================================================
# Forma recente
# =============================================================================


def get_team_recent_matches(
    matches: pd.DataFrame,
    team_id: int,
    last_n: int = 5,
) -> list[dict]:
    """
    Retorna os últimos jogos realizados de um clube.

    O resultado é exibido pela perspectiva do clube:

    V = vitória
    E = empate
    D = derrota
    """

    if last_n <= 0:

        raise ValueError(
            "last_n deve ser maior que zero."
        )

    played = get_played_matches(
        matches
    )

    team_matches = played[
        (
            played[
                "home_team_id"
            ]
            == team_id
        )
        |
        (
            played[
                "away_team_id"
            ]
            == team_id
        )
    ].copy()

    team_matches = (
        sort_matches_chronologically(
            team_matches
        )
    )

    team_matches = (
        team_matches.tail(
            last_n
        )
    )

    recent_matches = []

    for _, match in team_matches.iterrows():

        is_home = (
            int(
                match[
                    "home_team_id"
                ]
            )
            == int(
                team_id
            )
        )

        if is_home:

            goals_for = int(
                match[
                    "home_goals"
                ]
            )

            goals_against = int(
                match[
                    "away_goals"
                ]
            )

            opponent_id = int(
                match[
                    "away_team_id"
                ]
            )

            opponent = match[
                "away_team"
            ]

        else:

            goals_for = int(
                match[
                    "away_goals"
                ]
            )

            goals_against = int(
                match[
                    "home_goals"
                ]
            )

            opponent_id = int(
                match[
                    "home_team_id"
                ]
            )

            opponent = match[
                "home_team"
            ]

        if (
            goals_for
            > goals_against
        ):

            result = "V"

        elif (
            goals_for
            == goals_against
        ):

            result = "E"

        else:

            result = "D"

        recent_matches.append(
            {
                "match_id": (
                    int(
                        match[
                            "match_id"
                        ]
                    )
                    if (
                        "match_id"
                        in match
                        and pd.notna(
                            match[
                                "match_id"
                            ]
                        )
                    )
                    else None
                ),
                "round": (
                    int(
                        match[
                            "round"
                        ]
                    )
                    if (
                        "round"
                        in match
                        and pd.notna(
                            match[
                                "round"
                            ]
                        )
                    )
                    else None
                ),
                "date": (
                    match[
                        "date"
                    ]
                    if "date"
                    in match
                    else None
                ),
                "time": (
                    match[
                        "time"
                    ]
                    if "time"
                    in match
                    else None
                ),
                "home": is_home,
                "opponent_id": opponent_id,
                "opponent": opponent,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "result": result,
            }
        )

    return recent_matches


def get_recent_form_table(
    matches: pd.DataFrame,
    last_n: int = 5,
) -> pd.DataFrame:
    """
    Calcula a forma recente de todos os clubes.

    Por padrão considera os últimos 5 jogos.
    """

    if last_n <= 0:

        raise ValueError(
            "last_n deve ser maior que zero."
        )

    played = get_played_matches(
        matches
    )

    teams = get_teams(
        played
    )

    stats = []

    for _, team in teams.iterrows():

        team_id = int(
            team[
                "team_id"
            ]
        )

        recent = get_team_recent_matches(
            matches,
            team_id=team_id,
            last_n=last_n,
        )

        wins = sum(
            game[
                "result"
            ]
            == "V"
            for game
            in recent
        )

        draws = sum(
            game[
                "result"
            ]
            == "E"
            for game
            in recent
        )

        losses = sum(
            game[
                "result"
            ]
            == "D"
            for game
            in recent
        )

        points = (
            wins * 3
            + draws
        )

        goals_for = sum(
            game[
                "goals_for"
            ]
            for game
            in recent
        )

        goals_against = sum(
            game[
                "goals_against"
            ]
            for game
            in recent
        )

        goal_difference = (
            goals_for
            - goals_against
        )

        games_count = len(
            recent
        )

        performance = (
            (
                points
                / (
                    games_count
                    * 3
                )
                * 100
            )
            if games_count
            else 0
        )

        form = " ".join(
            game[
                "result"
            ]
            for game
            in recent
        )

        stats.append(
            {
                "team_id": team_id,
                "team": team[
                    "team"
                ],
                "recent_matches": games_count,
                "recent_wins": wins,
                "recent_draws": draws,
                "recent_losses": losses,
                "recent_points": points,
                "recent_goals_for": goals_for,
                "recent_goals_against": goals_against,
                "recent_goal_difference": goal_difference,
                "recent_performance_pct": round(
                    performance,
                    2,
                ),
                "recent_form": form,
            }
        )

    dataframe = pd.DataFrame(
        stats
    )

    if dataframe.empty:

        return dataframe

    dataframe = (
        dataframe.sort_values(
            by=[
                "recent_points",
                "recent_wins",
                "recent_goal_difference",
                "recent_goals_for",
            ],
            ascending=[
                False,
                False,
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    dataframe.insert(
        0,
        "recent_position",
        range(
            1,
            len(dataframe) + 1,
        ),
    )

    return dataframe


# =============================================================================
# Validação contra classificação oficial
# =============================================================================


def compare_with_official_standings(
    matches: pd.DataFrame,
    official_standings: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compara a classificação calculada a partir dos jogos
    com a classificação oficial coletada da CBF.
    """

    calculated = get_team_stats(
        matches
    )

    metrics = [
        "matches",
        "wins",
        "draws",
        "losses",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
    ]

    calculated_columns = [
        "team_id",
        "team",
        "calculated_position",
        *metrics,
    ]

    official_columns = [
        "team_id",
        "team",
        "position",
        *metrics,
    ]

    calculated_data = (
        calculated[
            calculated_columns
        ]
        .rename(
            columns={
                "team": (
                    "calculated_team"
                ),
                **{
                    metric: (
                        f"calculated_"
                        f"{metric}"
                    )
                    for metric
                    in metrics
                },
            }
        )
    )

    official_data = (
        official_standings[
            official_columns
        ]
        .rename(
            columns={
                "team": (
                    "official_team"
                ),
                "position": (
                    "official_position"
                ),
                **{
                    metric: (
                        f"official_"
                        f"{metric}"
                    )
                    for metric
                    in metrics
                },
            }
        )
    )

    comparison = (
        calculated_data.merge(
            official_data,
            on="team_id",
            how="outer",
            validate="one_to_one",
            indicator=True,
        )
    )

    for metric in metrics:

        comparison[
            f"{metric}_match"
        ] = (
            comparison[
                f"calculated_{metric}"
            ]
            == comparison[
                f"official_{metric}"
            ]
        )

    comparison[
        "position_match"
    ] = (
        comparison[
            "calculated_position"
        ]
        == comparison[
            "official_position"
        ]
    )

    metric_checks = [
        f"{metric}_match"
        for metric
        in metrics
    ]

    comparison[
        "all_stats_match"
    ] = (
        comparison[
            "_merge"
        ].eq(
            "both"
        )
        & comparison[
            metric_checks
        ].all(
            axis=1
        )
    )

    return (
        comparison.sort_values(
            by=(
                "official_position"
            ),
            na_position="last",
        )
        .reset_index(
            drop=True
        )
    )


# =============================================================================
# Exibição no terminal
# =============================================================================


def print_championship_summary(
    source: str = "csv",
) -> None:
    """
    Exibe o painel de análise do campeonato.

    source:
        csv
        database
    """

    matches = load_matches_by_source(
        source
    )

    official_standings = (
        load_standings()
    )

    summary = (
        get_championship_summary(
            matches
        )
    )

    team_stats = get_team_stats(
        matches
    )

    home_ranking = get_home_ranking(
        matches
    )

    away_ranking = get_away_ranking(
        matches
    )

    recent_form = (
        get_recent_form_table(
            matches,
            last_n=5,
        )
    )

    comparison = (
        compare_with_official_standings(
            matches,
            official_standings,
        )
    )

    source_label = (
        "SQLite"
        if source.lower()
        == "database"
        else "CSV"
    )

    print()
    print("⚽ Brasileirão Data Lab")
    print(
        "📊 V0.3 - Análise do Campeonato"
    )
    print("=" * 68)

    print(
        f"Fonte: {source_label}"
    )

    # -------------------------------------------------------------------------
    # Campeonato
    # -------------------------------------------------------------------------

    print()
    print("CAMPEONATO")
    print("-" * 68)

    print(
        f"Partidas previstas: "
        f"{summary['total_matches']}"
    )

    print(
        f"Partidas realizadas: "
        f"{summary['played_matches']}"
    )

    print(
        f"Partidas restantes: "
        f"{summary['future_matches']}"
    )

    print(
        f"Gols marcados: "
        f"{summary['total_goals']}"
    )

    print(
        f"Média de gols/jogo: "
        f"{summary['average_goals_per_match']:.2f}"
    )

    # -------------------------------------------------------------------------
    # Resultados
    # -------------------------------------------------------------------------

    print()
    print("RESULTADOS")
    print("-" * 68)

    print(
        f"Vitórias dos mandantes: "
        f"{summary['home_wins']}"
    )

    print(
        f"Empates: "
        f"{summary['draws']}"
    )

    print(
        f"Vitórias dos visitantes: "
        f"{summary['away_wins']}"
    )

    # -------------------------------------------------------------------------
    # Classificação
    # -------------------------------------------------------------------------

    if not team_stats.empty:

        top_five = (
            team_stats
            .head(
                5
            )
            .reset_index(
                drop=True
            )
        )

        expected_top_size = min(
            5,
            len(
                team_stats
            ),
        )

        if len(
            top_five
        ) != expected_top_size:

            raise RuntimeError(
                "Falha ao montar o Top 5 "
                "da classificação."
            )

        print()
        print(
            "TOP 5 - CLASSIFICAÇÃO CALCULADA"
        )
        print("-" * 68)

        for _, team in (
            top_five.iterrows()
        ):

            print(
                f"{int(team['calculated_position']):>2}º "
                f"{team['team']:<26} "
                f"{int(team['points']):>3} pts"
            )

        best_attack = team_stats.loc[
            team_stats[
                "goals_for"
            ].idxmax()
        ]

        best_defense = team_stats.loc[
            team_stats[
                "goals_against"
            ].idxmin()
        ]

        print()
        print("DESTAQUES")
        print("-" * 68)

        print(
            f"🔥 Melhor ataque: "
            f"{best_attack['team']} "
            f"("
            f"{int(best_attack['goals_for'])} "
            f"gols)"
        )

        print(
            f"🧱 Melhor defesa: "
            f"{best_defense['team']} "
            f"("
            f"{int(best_defense['goals_against'])} "
            f"sofridos)"
        )

    # -------------------------------------------------------------------------
    # Casa
    # -------------------------------------------------------------------------

    if not home_ranking.empty:

        print()
        print(
            "🏠 TOP 5 - MELHORES MANDANTES"
        )
        print("-" * 68)

        for _, team in (
            home_ranking.head(
                5
            ).iterrows()
        ):

            print(
                f"{int(team['home_position']):>2}º "
                f"{team['team']:<26} "
                f"{int(team['home_points']):>3} pts | "
                f"{team['home_performance_pct']:>6.2f}%"
            )

    # -------------------------------------------------------------------------
    # Fora
    # -------------------------------------------------------------------------

    if not away_ranking.empty:

        print()
        print(
            "✈️ TOP 5 - MELHORES VISITANTES"
        )
        print("-" * 68)

        for _, team in (
            away_ranking.head(
                5
            ).iterrows()
        ):

            print(
                f"{int(team['away_position']):>2}º "
                f"{team['team']:<26} "
                f"{int(team['away_points']):>3} pts | "
                f"{team['away_performance_pct']:>6.2f}%"
            )

    # -------------------------------------------------------------------------
    # Forma recente
    # -------------------------------------------------------------------------

    if not recent_form.empty:

        print()
        print(
            "🔥 TOP 5 - MELHOR MOMENTO "
            "(ÚLTIMOS 5)"
        )
        print("-" * 68)

        for _, team in (
            recent_form.head(
                5
            ).iterrows()
        ):

            print(
                f"{int(team['recent_position']):>2}º "
                f"{team['team']:<26} "
                f"{int(team['recent_points']):>2}/15 pts | "
                f"{team['recent_form']}"
            )

    # -------------------------------------------------------------------------
    # Validação
    # -------------------------------------------------------------------------

    total_teams = len(
        official_standings
    )

    exact_stats = int(
        comparison[
            "all_stats_match"
        ].sum()
    )

    matching_positions = int(
        comparison[
            "position_match"
        ].sum()
    )

    print()
    print(
        "VALIDAÇÃO CONTRA A CBF"
    )
    print("-" * 68)

    print(
        f"Estatísticas conferindo: "
        f"{exact_stats}/{total_teams} clubes"
    )

    print(
        f"Posições conferindo: "
        f"{matching_positions}/{total_teams} clubes"
    )

    if (
        exact_stats
        == total_teams
        and matching_positions
        == total_teams
    ):

        print(
            "✅ Dados calculados conferem "
            "com a classificação oficial."
        )

    else:

        print()
        print(
            "⚠️ Divergências encontradas:"
        )

        divergent = comparison[
            ~comparison[
                "all_stats_match"
            ]
            |
            ~comparison[
                "position_match"
            ]
        ]

        for _, team in (
            divergent.iterrows()
        ):

            team_name = (
                team[
                    "official_team"
                ]
                if pd.notna(
                    team[
                        "official_team"
                    ]
                )
                else team[
                    "calculated_team"
                ]
            )

            print(
                f" - {team_name}"
            )

    print()
    print("=" * 68)


# =============================================================================
# CLI
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Cria os argumentos da CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "Análise do Campeonato Brasileiro."
        )
    )

    parser.add_argument(
        "--source",
        choices=[
            "csv",
            "database",
        ],
        default="csv",
        help=(
            "Fonte dos dados das partidas. "
            "Padrão: csv."
        ),
    )

    return parser


def main() -> None:
    """Executa a CLI."""

    parser = create_parser()

    args = parser.parse_args()

    print_championship_summary(
        source=args.source
    )


if __name__ == "__main__":
    main()