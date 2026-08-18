from __future__ import annotations

from pathlib import Path

import matplotlib

# Backend não interativo.
# Permite gerar e salvar gráficos sem abrir janelas.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from brasileirao_data_lab.analytics.championship import (
    get_home_away_stats,
    get_team_stats,
    load_matches,
)
from brasileirao_data_lab.analytics.evolution import (
    get_position_history,
)


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a pasta raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_figures_dir() -> Path:
    """Retorna a pasta onde os gráficos serão salvos."""

    directory = (
        get_project_root()
        / "reports"
        / "figures"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def resolve_output_path(
    filename: str,
    output_dir: Path | str | None = None,
) -> Path:
    """Monta o caminho final de um gráfico."""

    if output_dir is None:
        directory = get_figures_dir()

    else:
        directory = Path(output_dir)

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    return directory / filename


# =============================================================================
# Validações
# =============================================================================


def validate_top_n(
    top_n: int,
) -> None:
    """Valida a quantidade de clubes exibidos."""

    if top_n <= 0:
        raise ValueError(
            "top_n deve ser maior que zero."
        )


def get_top_team_ids(
    matches: pd.DataFrame,
    top_n: int,
) -> list[int]:
    """
    Retorna os IDs dos melhores clubes
    da classificação atual calculada.
    """

    validate_top_n(
        top_n
    )

    standings = get_team_stats(
        matches
    )

    if standings.empty:
        return []

    return [
        int(team_id)
        for team_id in (
            standings
            .head(top_n)["team_id"]
            .tolist()
        )
    ]


# =============================================================================
# Evolução de posição
# =============================================================================


def plot_position_evolution(
    matches: pd.DataFrame,
    top_n: int = 8,
    output_dir: Path | str | None = None,
) -> Path:
    """
    Gera um gráfico da posição rodada por rodada.

    Para evitar excesso de linhas, por padrão
    exibe os 8 primeiros colocados atuais.
    """

    validate_top_n(
        top_n
    )

    history = get_position_history(
        matches
    )

    if history.empty:
        raise ValueError(
            "Não existem dados suficientes "
            "para gerar o gráfico de posições."
        )

    team_ids = get_top_team_ids(
        matches,
        top_n=top_n,
    )

    selected = history[
        history["team_id"].isin(
            team_ids
        )
    ].copy()

    figure, axis = plt.subplots(
        figsize=(14, 8)
    )

    for team_id in team_ids:

        team_history = selected[
            selected["team_id"] == team_id
        ].sort_values(
            "round"
        )

        if team_history.empty:
            continue

        team_name = (
            team_history.iloc[-1]["team"]
        )

        axis.plot(
            team_history["round"],
            team_history["position"],
            marker="o",
            markersize=3,
            linewidth=2,
            label=team_name,
        )

    maximum_position = int(
        history["position"].max()
    )

    maximum_round = int(
        history["round"].max()
    )

    axis.set_ylim(
        maximum_position + 0.5,
        0.5,
    )

    axis.set_xlim(
        1,
        maximum_round,
    )

    axis.set_yticks(
        range(
            1,
            maximum_position + 1,
        )
    )

    axis.set_xticks(
        range(
            1,
            maximum_round + 1,
        )
    )

    axis.set_xlabel(
        "Rodada"
    )

    axis.set_ylabel(
        "Posição"
    )

    axis.set_title(
        f"Evolução da classificação "
        f"do Brasileirão\n"
        f"Top {len(team_ids)} atual"
    )

    axis.grid(
        alpha=0.25
    )

    axis.legend(
        title="Clubes",
        bbox_to_anchor=(
            1.02,
            1,
        ),
        loc="upper left",
    )

    figure.tight_layout()

    output_file = resolve_output_path(
        "position_evolution.png",
        output_dir=output_dir,
    )

    figure.savefig(
        output_file,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )

    return output_file


# =============================================================================
# Evolução de pontos
# =============================================================================


def plot_points_evolution(
    matches: pd.DataFrame,
    top_n: int = 8,
    output_dir: Path | str | None = None,
) -> Path:
    """
    Gera a evolução da pontuação acumulada
    rodada por rodada.
    """

    validate_top_n(
        top_n
    )

    history = get_position_history(
        matches
    )

    if history.empty:
        raise ValueError(
            "Não existem dados suficientes "
            "para gerar o gráfico de pontos."
        )

    team_ids = get_top_team_ids(
        matches,
        top_n=top_n,
    )

    selected = history[
        history["team_id"].isin(
            team_ids
        )
    ].copy()

    figure, axis = plt.subplots(
        figsize=(14, 8)
    )

    for team_id in team_ids:

        team_history = selected[
            selected["team_id"] == team_id
        ].sort_values(
            "round"
        )

        if team_history.empty:
            continue

        team_name = (
            team_history.iloc[-1]["team"]
        )

        axis.plot(
            team_history["round"],
            team_history["points"],
            marker="o",
            markersize=3,
            linewidth=2,
            label=team_name,
        )

    maximum_round = int(
        history["round"].max()
    )

    axis.set_xlim(
        1,
        maximum_round,
    )

    axis.set_xticks(
        range(
            1,
            maximum_round + 1,
        )
    )

    axis.set_xlabel(
        "Rodada"
    )

    axis.set_ylabel(
        "Pontos acumulados"
    )

    axis.set_title(
        f"Evolução de pontos "
        f"do Brasileirão\n"
        f"Top {len(team_ids)} atual"
    )

    axis.grid(
        alpha=0.25
    )

    axis.legend(
        title="Clubes",
        bbox_to_anchor=(
            1.02,
            1,
        ),
        loc="upper left",
    )

    figure.tight_layout()

    output_file = resolve_output_path(
        "points_evolution.png",
        output_dir=output_dir,
    )

    figure.savefig(
        output_file,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )

    return output_file


# =============================================================================
# Casa x fora
# =============================================================================


def plot_home_away_performance(
    matches: pd.DataFrame,
    top_n: int = 10,
    output_dir: Path | str | None = None,
) -> Path:
    """
    Compara o aproveitamento dos clubes
    jogando em casa e fora.

    Os clubes exibidos são os melhores
    colocados na classificação atual.
    """

    validate_top_n(
        top_n
    )

    standings = get_team_stats(
        matches
    )

    venue_stats = get_home_away_stats(
        matches
    )

    if standings.empty or venue_stats.empty:
        raise ValueError(
            "Não existem dados suficientes "
            "para gerar o gráfico casa x fora."
        )

    top_teams = standings.head(
        top_n
    )[
        [
            "team_id",
            "team",
        ]
    ].copy()

    selected = top_teams.merge(
        venue_stats[
            [
                "team_id",
                "home_performance_pct",
                "away_performance_pct",
            ]
        ],
        on="team_id",
        how="left",
        validate="one_to_one",
    )

    positions = list(
        range(
            len(selected)
        )
    )

    width = 0.38

    home_positions = [
        position - width / 2
        for position in positions
    ]

    away_positions = [
        position + width / 2
        for position in positions
    ]

    figure, axis = plt.subplots(
        figsize=(14, 8)
    )

    axis.bar(
        home_positions,
        selected[
            "home_performance_pct"
        ],
        width=width,
        label="Casa",
    )

    axis.bar(
        away_positions,
        selected[
            "away_performance_pct"
        ],
        width=width,
        label="Fora",
    )

    axis.set_xticks(
        positions
    )

    axis.set_xticklabels(
        selected["team"],
        rotation=40,
        ha="right",
    )

    axis.set_ylabel(
        "Aproveitamento (%)"
    )

    axis.set_xlabel(
        "Clube"
    )

    axis.set_title(
        "Aproveitamento em casa "
        "x aproveitamento fora\n"
        f"Top {len(selected)} da classificação"
    )

    axis.set_ylim(
        0,
        100,
    )

    axis.grid(
        axis="y",
        alpha=0.25,
    )

    axis.legend()

    figure.tight_layout()

    output_file = resolve_output_path(
        "home_away_performance.png",
        output_dir=output_dir,
    )

    figure.savefig(
        output_file,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )

    return output_file


# =============================================================================
# Geração completa
# =============================================================================


def generate_all_charts(
    matches: pd.DataFrame | None = None,
    output_dir: Path | str | None = None,
) -> list[Path]:
    """
    Gera todos os gráficos principais
    da V0.2.
    """

    if matches is None:
        matches = load_matches()

    files = [
        plot_position_evolution(
            matches,
            top_n=8,
            output_dir=output_dir,
        ),
        plot_points_evolution(
            matches,
            top_n=8,
            output_dir=output_dir,
        ),
        plot_home_away_performance(
            matches,
            top_n=10,
            output_dir=output_dir,
        ),
    ]

    return files


# =============================================================================
# Terminal
# =============================================================================


def print_visualization_summary() -> None:
    """Gera os gráficos e exibe os caminhos."""

    print()
    print("⚽ Brasileirão Data Lab")
    print("📈 V0.2 - Visualizações")
    print("=" * 70)

    print()
    print(
        "[INFO] Gerando gráficos..."
    )

    files = generate_all_charts()

    print()

    for file_path in files:

        print(
            f"[SUCCESS] "
            f"{file_path.name}"
        )

        print(
            f"          {file_path}"
        )

    print()
    print(
        f"[SUCCESS] "
        f"{len(files)} gráficos gerados."
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    print_visualization_summary()