from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path

import matplotlib

# Backend não interativo.
# Permite gerar PNG sem abrir janela.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from brasileirao_data_lab.analytics.championship import (
    get_team_stats,
    load_matches,
)
from brasileirao_data_lab.analytics.comparison import (
    resolve_team,
)
from brasileirao_data_lab.analytics.evolution import (
    get_team_position_history,
)
from brasileirao_data_lab.analytics.team_report import (
    format_date,
    format_time,
    get_team_report,
)


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_team_figures_dir() -> Path:
    """
    Retorna a pasta padrão dos gráficos individuais.
    """

    directory = (
        get_project_root()
        / "reports"
        / "figures"
        / "teams"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


# =============================================================================
# Nome de arquivo
# =============================================================================


def slugify_team_name(
    team_name: str,
) -> str:
    """
    Converte o nome do clube para um formato
    seguro para nome de arquivo.

    Exemplo:

    Atlético Mineiro
    ->
    atletico_mineiro
    """

    normalized = unicodedata.normalize(
        "NFKD",
        team_name,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    cleaned = []

    for character in normalized.casefold():

        if character.isalnum():

            cleaned.append(
                character
            )

        elif character in {
            " ",
            "-",
            "_",
        }:

            cleaned.append(
                "_"
            )

    slug = "".join(
        cleaned
    )

    while "__" in slug:

        slug = slug.replace(
            "__",
            "_",
        )

    return slug.strip(
        "_"
    )


# =============================================================================
# Utilidades
# =============================================================================


def get_form_symbol(
    result: str,
) -> str:
    """Retorna uma representação textual da forma."""

    mapping = {
        "V": "V",
        "E": "E",
        "D": "D",
    }

    return mapping.get(
        result,
        "?",
    )


def resolve_output_path(
    team_name: str,
    output_dir: Path | str | None = None,
) -> Path:
    """Retorna o caminho final do PNG."""

    if output_dir is None:

        directory = (
            get_team_figures_dir()
        )

    else:

        directory = Path(
            output_dir
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    filename = (
        f"{slugify_team_name(team_name)}"
        "_report.png"
    )

    return (
        directory
        / filename
    )


def build_recent_form_text(
    recent_matches: list[dict],
) -> str:
    """Monta a sequência dos últimos resultados."""

    if not recent_matches:
        return "-"

    return "  ".join(
        get_form_symbol(
            game["result"]
        )
        for game in recent_matches
    )


def build_next_match_text(
    next_match: dict | None,
) -> str:
    """Monta o texto resumido do próximo jogo."""

    if next_match is None:

        return (
            "Nenhuma partida futura encontrada."
        )

    location = (
        "Casa"
        if next_match["home"]
        else "Fora"
    )

    round_text = (
        f"R{next_match['round']}"
        if next_match["round"] is not None
        else "Rodada a definir"
    )

    opponent = (
        next_match["opponent"]
    )

    date_text = format_date(
        next_match["date"]
    )

    time_text = format_time(
        next_match["time"]
    )

    venue = (
        next_match["venue"]
        or "Estádio a definir"
    )

    return "\n".join(
        [
            f"{round_text} | {opponent}",
            location,
            f"{date_text} | {time_text}",
            venue,
        ]
    )


# =============================================================================
# Painel visual
# =============================================================================


def plot_team_report(
    matches: pd.DataFrame,
    team_id: int,
    output_dir: Path | str | None = None,
) -> Path:
    """
    Gera o painel visual completo de um clube.
    """

    report = get_team_report(
        matches,
        team_id=team_id,
        recent_n=5,
    )

    profile = report[
        "profile"
    ]

    averages = report[
        "averages"
    ]

    evolution = report[
        "evolution"
    ]

    recent_matches = report[
        "recent_matches"
    ]

    next_match = report[
        "next_match"
    ]

    history = get_team_position_history(
        matches,
        team_id=team_id,
    )

    if history.empty:

        raise ValueError(
            "Não existem dados suficientes "
            "para gerar o gráfico do clube."
        )

    # =========================================================================
    # Figura
    # =========================================================================

    figure = plt.figure(
        figsize=(15, 10.5)
    )

    grid = figure.add_gridspec(
        nrows=2,
        ncols=2,
        hspace=0.34,
        wspace=0.26,
    )

    position_axis = (
        figure.add_subplot(
            grid[0, 0]
        )
    )

    venue_axis = (
        figure.add_subplot(
            grid[0, 1]
        )
    )

    goals_axis = (
        figure.add_subplot(
            grid[1, 0]
        )
    )

    info_axis = (
        figure.add_subplot(
            grid[1, 1]
        )
    )

    # Espaço reservado para título e rodapé.
    figure.subplots_adjust(
        top=0.88,
        bottom=0.09,
    )

    # =========================================================================
    # Cabeçalho
    # =========================================================================

    figure.suptitle(
        (
            f"{profile['team']}\n"
            f"{profile['position']}º lugar | "
            f"{profile['points']} pts | "
            f"{profile['matches']} jogos"
        ),
        fontsize=19,
        fontweight="bold",
        y=0.965,
    )

    # =========================================================================
    # Evolução de posição
    # =========================================================================

    position_axis.plot(
        history["round"],
        history["position"],
        marker="o",
        linewidth=2,
        markersize=4,
    )

    maximum_position = max(
        int(
            history["position"].max()
        ),
        1,
    )

    position_axis.set_ylim(
        maximum_position + 0.5,
        0.5,
    )

    position_axis.set_xlabel(
        "Rodada"
    )

    position_axis.set_ylabel(
        "Posição"
    )

    position_axis.set_title(
        "Evolução na classificação",
        fontweight="bold",
    )

    position_axis.grid(
        alpha=0.25
    )

    round_values = (
        history["round"]
        .dropna()
        .astype(int)
        .unique()
    )

    if len(round_values) <= 25:

        position_axis.set_xticks(
            sorted(
                round_values
            )
        )

    position_axis.set_yticks(
        range(
            1,
            maximum_position + 1,
        )
    )

    # =========================================================================
    # Casa x fora
    # =========================================================================

    venue_labels = [
        "Casa",
        "Fora",
    ]

    venue_values = [
        profile[
            "home_performance_pct"
        ],
        profile[
            "away_performance_pct"
        ],
    ]

    bars = venue_axis.bar(
        venue_labels,
        venue_values,
    )

    venue_axis.set_ylim(
        0,
        100,
    )

    venue_axis.set_ylabel(
        "Aproveitamento (%)"
    )

    venue_axis.set_title(
        "Desempenho em casa x fora",
        fontweight="bold",
    )

    venue_axis.grid(
        axis="y",
        alpha=0.25,
    )

    for bar, value in zip(
        bars,
        venue_values,
    ):

        venue_axis.text(
            bar.get_x()
            + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
        )

    # =========================================================================
    # Gols
    # =========================================================================

    goal_labels = [
        "Marcados",
        "Sofridos",
    ]

    goal_values = [
        profile[
            "goals_for"
        ],
        profile[
            "goals_against"
        ],
    ]

    goal_bars = goals_axis.bar(
        goal_labels,
        goal_values,
    )

    goals_axis.set_ylabel(
        "Gols"
    )

    goals_axis.set_title(
        "Produção ofensiva e defensiva",
        fontweight="bold",
    )

    goals_axis.grid(
        axis="y",
        alpha=0.25,
    )

    maximum_goals = max(
        goal_values
    )

    goals_axis.set_ylim(
        0,
        maximum_goals * 1.15
        if maximum_goals > 0
        else 1,
    )

    for bar, value in zip(
        goal_bars,
        goal_values,
    ):

        goals_axis.text(
            bar.get_x()
            + bar.get_width() / 2,
            bar.get_height()
            + max(
                maximum_goals * 0.015,
                0.2,
            ),
            str(value),
            ha="center",
            va="bottom",
            fontsize=11,
        )

    # =========================================================================
    # Painel de informações
    # =========================================================================

    info_axis.axis(
        "off"
    )

    recent_form = (
        build_recent_form_text(
            recent_matches
        )
    )

    next_match_text = (
        build_next_match_text(
            next_match
        )
    )

    # -------------------------------------------------------------------------
    # Momento atual
    # -------------------------------------------------------------------------

    info_axis.text(
        0.02,
        0.96,
        "MOMENTO ATUAL",
        transform=info_axis.transAxes,
        va="top",
        ha="left",
        fontsize=12,
        fontweight="bold",
    )

    info_axis.text(
        0.02,
        0.87,
        (
            f"Últimos 5: {recent_form}\n"
            f"Pontos recentes: "
            f"{profile['recent_points']}/15\n"
            f"Aproveitamento recente: "
            f"{profile['recent_performance_pct']:.2f}%"
        ),
        transform=info_axis.transAxes,
        va="top",
        ha="left",
        fontsize=11,
        linespacing=1.35,
    )

    # -------------------------------------------------------------------------
    # Médias
    # -------------------------------------------------------------------------

    info_axis.text(
        0.02,
        0.67,
        "MÉDIAS",
        transform=info_axis.transAxes,
        va="top",
        ha="left",
        fontsize=12,
        fontweight="bold",
    )

    info_axis.text(
        0.02,
        0.58,
        (
            f"Pontos/jogo: "
            f"{averages['points_per_match']:.2f}\n"
            f"Gols marcados/jogo: "
            f"{averages['goals_for_per_match']:.2f}\n"
            f"Gols sofridos/jogo: "
            f"{averages['goals_against_per_match']:.2f}"
        ),
        transform=info_axis.transAxes,
        va="top",
        ha="left",
        fontsize=11,
        linespacing=1.35,
    )

    # -------------------------------------------------------------------------
    # Histórico
    # -------------------------------------------------------------------------

    info_axis.text(
        0.02,
        0.38,
        "HISTÓRICO",
        transform=info_axis.transAxes,
        va="top",
        ha="left",
        fontsize=12,
        fontweight="bold",
    )

    info_axis.text(
        0.02,
        0.29,
        (
            f"Melhor posição: "
            f"{evolution['best_position']}º\n"
            f"Pior posição: "
            f"{evolution['worst_position']}º"
        ),
        transform=info_axis.transAxes,
        va="top",
        ha="left",
        fontsize=11,
        linespacing=1.35,
    )

    # -------------------------------------------------------------------------
    # Próximo jogo
    # -------------------------------------------------------------------------

    info_axis.text(
        0.54,
        0.38,
        "PRÓXIMO JOGO",
        transform=info_axis.transAxes,
        va="top",
        ha="left",
        fontsize=12,
        fontweight="bold",
    )

    info_axis.text(
        0.54,
        0.29,
        next_match_text,
        transform=info_axis.transAxes,
        va="top",
        ha="left",
        fontsize=11,
        linespacing=1.35,
    )

    # =========================================================================
    # Rodapé
    # =========================================================================

    figure.text(
        0.5,
        0.028,
        (
            "Brasileirão Data Lab | "
            "Dados coletados da CBF"
        ),
        ha="center",
        fontsize=9,
        alpha=0.7,
    )

    # =========================================================================
    # Salvar
    # =========================================================================

    output_file = resolve_output_path(
        profile["team"],
        output_dir=output_dir,
    )

    figure.savefig(
        output_file,
        dpi=170,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )

    return output_file


# =============================================================================
# Geração por nome / ID
# =============================================================================


def generate_team_visualization(
    team_identifier: int | str | None = None,
    output_dir: Path | str | None = None,
) -> Path:
    """
    Gera o painel visual utilizando
    nome ou ID do clube.

    Sem argumento utiliza o líder atual.
    """

    matches = load_matches()

    if team_identifier is None:

        standings = get_team_stats(
            matches
        )

        if standings.empty:

            raise ValueError(
                "Não existem partidas realizadas."
            )

        team_id = int(
            standings.iloc[0][
                "team_id"
            ]
        )

    else:

        team = resolve_team(
            matches,
            team_identifier,
        )

        team_id = int(
            team["team_id"]
        )

    return plot_team_report(
        matches,
        team_id=team_id,
        output_dir=output_dir,
    )


# =============================================================================
# Terminal
# =============================================================================


def print_team_visualization_summary(
    team_identifier: int | str | None = None,
) -> None:
    """Gera o painel e exibe o caminho."""

    print()
    print("⚽ Brasileirão Data Lab")
    print("🎨 V0.2 - Painel Visual do Clube")
    print("=" * 70)

    print()
    print(
        "[INFO] Gerando painel..."
    )

    output_file = (
        generate_team_visualization(
            team_identifier
        )
    )

    print()
    print(
        f"[SUCCESS] "
        f"{output_file.name}"
    )

    print(
        f"          "
        f"{output_file}"
    )

    print()
    print("=" * 70)


# =============================================================================
# CLI
# =============================================================================


def main() -> None:
    """Entrada do módulo."""

    parser = argparse.ArgumentParser(
        description=(
            "Gera o painel visual "
            "de um clube."
        )
    )

    parser.add_argument(
        "team",
        nargs="?",
        help=(
            "Nome ou ID do clube. "
            "Sem valor utiliza o líder."
        ),
    )

    args = parser.parse_args()

    print_team_visualization_summary(
        args.team
    )


if __name__ == "__main__":
    main()