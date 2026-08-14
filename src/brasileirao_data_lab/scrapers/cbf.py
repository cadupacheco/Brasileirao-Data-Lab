from pathlib import Path

import truststore

truststore.inject_into_ssl()

import pandas as pd
import requests
from bs4 import BeautifulSoup


CBF_SERIE_A_URL = (
    "https://www.cbf.com.br/"
    "futebol-brasileiro/tabelas/"
    "campeonato-brasileiro/serie-a/2026"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}


def get_project_root() -> Path:
    """Retorna a pasta raiz do projeto."""
    return Path(__file__).resolve().parents[3]


def fetch_cbf_page() -> str:
    """Baixa o HTML da página da Série A no site da CBF."""

    response = requests.get(
        CBF_SERIE_A_URL,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def save_raw_html(html: str) -> Path:
    """Salva o HTML bruto coletado para análise."""

    output_dir = get_project_root() / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "cbf_serie_a_2026.html"

    output_file.write_text(
        html,
        encoding="utf-8",
    )

    return output_file


def find_standings_table(soup: BeautifulSoup):
    """Localiza a tabela de classificação no HTML."""

    for table in soup.find_all("table"):
        headers = [
            th.get_text(" ", strip=True)
            for th in table.find_all("th")
        ]

        if any("Classificação" in header for header in headers):
            return table

    raise ValueError("Tabela de classificação não encontrada.")


def extract_team_id(href: str) -> int | None:
    """Extrai o ID do clube a partir da URL da CBF."""

    if not href:
        return None

    team_id = href.rstrip("/").split("/")[-1]

    if team_id.isdigit():
        return int(team_id)

    return None


def parse_standings(html: str) -> list[dict]:
    """Extrai a classificação do Campeonato Brasileiro."""

    soup = BeautifulSoup(html, "lxml")

    table = find_standings_table(soup)

    standings = []

    rows = table.find_all("tr")[1:]

    for row in rows:
        cells = row.find_all("td")

        if len(cells) < 12:
            continue

        team_cell = cells[0]

        position_element = team_cell.find("strong")
        team_link = team_cell.find("a", href=True)

        if not position_element or not team_link:
            continue

        position = int(position_element.get_text(strip=True))
        team = team_link.get_text(" ", strip=True)
        team_id = extract_team_id(team_link.get("href"))

        next_opponent_id = None

        if len(cells) > 13:
            next_link = cells[13].find("a", href=True)

            if next_link:
                next_opponent_id = extract_team_id(
                    next_link.get("href")
                )

        standings.append(
            {
                "position": position,
                "team_id": team_id,
                "team": team,
                "points": int(cells[1].get_text(strip=True)),
                "matches": int(cells[2].get_text(strip=True)),
                "wins": int(cells[3].get_text(strip=True)),
                "draws": int(cells[4].get_text(strip=True)),
                "losses": int(cells[5].get_text(strip=True)),
                "goals_for": int(cells[6].get_text(strip=True)),
                "goals_against": int(cells[7].get_text(strip=True)),
                "goal_difference": int(cells[8].get_text(strip=True)),
                "yellow_cards": int(cells[9].get_text(strip=True)),
                "red_cards": int(cells[10].get_text(strip=True)),
                "performance_pct": int(cells[11].get_text(strip=True)),
                "next_opponent_id": next_opponent_id,
            }
        )

    return standings


def resolve_next_opponents(
    standings: list[dict],
) -> list[dict]:
    """Converte o ID do próximo adversário para o nome do clube."""

    teams_by_id = {
        team["team_id"]: team["team"]
        for team in standings
        if team["team_id"] is not None
    }

    for team in standings:
        opponent_id = team.pop("next_opponent_id")

        team["next_opponent"] = teams_by_id.get(
            opponent_id
        )

    return standings


def save_standings_csv(
    standings: list[dict],
) -> Path:
    """Salva a classificação tratada em CSV."""

    output_dir = get_project_root() / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "standings.csv"

    dataframe = pd.DataFrame(standings)

    dataframe.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    return output_file


if __name__ == "__main__":
    print()
    print("⚽ Brasileirão Data Lab")
    print("=" * 40)

    print("[INFO] Acessando a CBF...")

    html = fetch_cbf_page()

    print(
        f"[SUCCESS] Página coletada: "
        f"{len(html):,} caracteres"
    )

    raw_file = save_raw_html(html)

    print(
        f"[SUCCESS] HTML bruto salvo em: "
        f"{raw_file}"
    )

    print("[INFO] Extraindo classificação...")

    standings = parse_standings(html)

    standings = resolve_next_opponents(
        standings
    )

    print(
        f"[SUCCESS] {len(standings)} clubes encontrados."
    )

    csv_file = save_standings_csv(
        standings
    )

    print(
        f"[SUCCESS] Classificação salva em: "
        f"{csv_file}"
    )

    print()
    print("Top 5:")
    print("-" * 40)

    for team in standings[:5]:
        print(
            f"{team['position']:>2}º "
            f"{team['team']:<25} "
            f"{team['points']:>2} pts"
        )

    print()
    print("[SUCCESS] Coleta concluída.")