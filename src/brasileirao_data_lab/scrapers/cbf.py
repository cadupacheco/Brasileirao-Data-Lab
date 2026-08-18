from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import truststore
from bs4 import BeautifulSoup


# =============================================================================
# SSL
# =============================================================================

# Faz o Python utilizar os certificados confiáveis do Windows.
truststore.inject_into_ssl()


# =============================================================================
# Configurações da CBF
# =============================================================================

CBF_SEASON = 2026
CBF_CHAMPIONSHIP_ID = 1260611
TOTAL_ROUNDS = 38

CBF_SERIE_A_URL = (
    "https://www.cbf.com.br/"
    "futebol-brasileiro/tabelas/"
    f"campeonato-brasileiro/serie-a/{CBF_SEASON}"
)

CBF_MATCHES_URL = (
    "https://www.cbf.com.br/api/cbf/jogos/"
    "campeonato/{championship_id}/"
    "rodada/{round_number}/fase"
)

HEADERS = {
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Referer": CBF_SERIE_A_URL,
}


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a pasta raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_raw_data_dir() -> Path:
    """Retorna a pasta de dados brutos."""

    directory = get_project_root() / "data" / "raw"
    directory.mkdir(parents=True, exist_ok=True)

    return directory


def get_processed_data_dir() -> Path:
    """Retorna a pasta de dados processados."""

    directory = get_project_root() / "data" / "processed"
    directory.mkdir(parents=True, exist_ok=True)

    return directory


# =============================================================================
# Cliente HTTP
# =============================================================================


def create_session() -> requests.Session:
    """Cria uma sessão HTTP reutilizável para acessar a CBF."""

    session = requests.Session()
    session.headers.update(HEADERS)

    return session


# =============================================================================
# Classificação
# =============================================================================


def fetch_cbf_page(
    session: requests.Session | None = None,
) -> str:
    """Baixa o HTML da página da Série A."""

    http = session or create_session()

    response = http.get(
        CBF_SERIE_A_URL,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def save_raw_html(html: str) -> Path:
    """Salva o HTML bruto da página da competição."""

    output_file = (
        get_raw_data_dir()
        / f"cbf_serie_a_{CBF_SEASON}.html"
    )

    output_file.write_text(
        html,
        encoding="utf-8",
    )

    return output_file


def find_standings_table(
    soup: BeautifulSoup,
):
    """Localiza a tabela de classificação."""

    for table in soup.find_all("table"):

        headers = [
            th.get_text(" ", strip=True)
            for th in table.find_all("th")
        ]

        if any(
            "Classificação" in header
            for header in headers
        ):
            return table

    raise ValueError(
        "Tabela de classificação não encontrada."
    )


def extract_team_id(
    href: str | None,
) -> int | None:
    """Extrai o ID do clube a partir de uma URL da CBF."""

    if not href:
        return None

    value = href.rstrip("/").split("/")[-1]

    if value.isdigit():
        return int(value)

    return None


def parse_standings(
    html: str,
) -> list[dict[str, Any]]:
    """Extrai os dados da classificação."""

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    table = find_standings_table(soup)

    standings: list[dict[str, Any]] = []

    rows = table.find_all("tr")[1:]

    for row in rows:

        cells = row.find_all("td")

        if len(cells) < 12:
            continue

        team_cell = cells[0]

        position_element = team_cell.find("strong")
        team_link = team_cell.find(
            "a",
            href=True,
        )

        if not position_element or not team_link:
            continue

        position = int(
            position_element.get_text(
                strip=True
            )
        )

        team = team_link.get_text(
            " ",
            strip=True,
        )

        team_id = extract_team_id(
            team_link.get("href")
        )

        next_opponent_id = None

        if len(cells) > 13:

            next_link = cells[13].find(
                "a",
                href=True,
            )

            if next_link:

                next_opponent_id = extract_team_id(
                    next_link.get("href")
                )

        standings.append(
            {
                "position": position,
                "team_id": team_id,
                "team": team,
                "points": int(
                    cells[1].get_text(
                        strip=True
                    )
                ),
                "matches": int(
                    cells[2].get_text(
                        strip=True
                    )
                ),
                "wins": int(
                    cells[3].get_text(
                        strip=True
                    )
                ),
                "draws": int(
                    cells[4].get_text(
                        strip=True
                    )
                ),
                "losses": int(
                    cells[5].get_text(
                        strip=True
                    )
                ),
                "goals_for": int(
                    cells[6].get_text(
                        strip=True
                    )
                ),
                "goals_against": int(
                    cells[7].get_text(
                        strip=True
                    )
                ),
                "goal_difference": int(
                    cells[8].get_text(
                        strip=True
                    )
                ),
                "yellow_cards": int(
                    cells[9].get_text(
                        strip=True
                    )
                ),
                "red_cards": int(
                    cells[10].get_text(
                        strip=True
                    )
                ),
                "performance_pct": int(
                    cells[11].get_text(
                        strip=True
                    )
                ),
                "next_opponent_id": next_opponent_id,
            }
        )

    return standings


def resolve_next_opponents(
    standings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Relaciona o ID do próximo adversário ao nome do clube."""

    teams_by_id = {
        team["team_id"]: team["team"]
        for team in standings
        if team["team_id"] is not None
    }

    for team in standings:

        opponent_id = team.get(
            "next_opponent_id"
        )

        team["next_opponent"] = (
            teams_by_id.get(opponent_id)
        )

    return standings


def save_standings_csv(
    standings: list[dict[str, Any]],
) -> Path:
    """Salva a classificação em CSV."""

    output_file = (
        get_processed_data_dir()
        / "standings.csv"
    )

    dataframe = pd.DataFrame(
        standings
    )

    dataframe.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    return output_file


# =============================================================================
# Jogos
# =============================================================================


def fetch_round(
    round_number: int,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Busca todos os jogos de uma rodada."""

    if not 1 <= round_number <= TOTAL_ROUNDS:
        raise ValueError(
            f"A rodada deve estar entre "
            f"1 e {TOTAL_ROUNDS}."
        )

    url = CBF_MATCHES_URL.format(
        championship_id=CBF_CHAMPIONSHIP_ID,
        round_number=round_number,
    )

    http = session or create_session()

    response = http.get(
        url,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def parse_optional_int(
    value: Any,
) -> int | None:
    """Converte um valor opcional para inteiro."""

    if value is None:
        return None

    if value == "":
        return None

    return int(value)


def normalize_optional_text(
    value: str | None,
) -> str | None:
    """
    Normaliza textos opcionais retornados pela CBF.

    Valores como "A Definir" são convertidos para None,
    pois ainda não representam uma informação confirmada.
    """

    if value is None:
        return None

    clean_value = str(value).strip()

    if not clean_value:
        return None

    undefined_values = {
        "a definir",
        "a confirmar",
        "não definido",
        "nao definido",
    }

    if clean_value.casefold() in undefined_values:
        return None

    return clean_value


def parse_match_date(
    value: str | None,
) -> str | None:
    """
    Converte DD/MM/YYYY para YYYY-MM-DD.

    Datas ainda não definidas pela CBF retornam None.
    """

    clean_value = normalize_optional_text(
        value
    )

    if clean_value is None:
        return None

    try:
        parsed_date = datetime.strptime(
            clean_value,
            "%d/%m/%Y",
        )

    except ValueError as exc:
        raise ValueError(
            "Formato de data inesperado "
            f"recebido da CBF: {value!r}"
        ) from exc

    return parsed_date.date().isoformat()


def parse_match_time(
    value: str | None,
) -> str | None:
    """
    Normaliza o horário de uma partida.

    Horários ainda não definidos retornam None.
    """

    return normalize_optional_text(
        value
    )


def parse_location(
    value: str | None,
) -> tuple[
    str | None,
    str | None,
    str | None,
]:
    """
    Divide o local em estádio, cidade e estado.

    Exemplo:
    Neo Química Arena - Sao Paulo - SP
    """

    if not value:
        return None, None, None

    parts = value.rsplit(
        " - ",
        2,
    )

    if len(parts) == 3:

        venue, city, state = parts

        return (
            venue.strip(),
            city.strip(),
            state.strip(),
        )

    return (
        value.strip(),
        None,
        None,
    )


def parse_round_matches(
    data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Normaliza os jogos retornados pela API da CBF."""

    matches: list[dict[str, Any]] = []

    groups = data.get(
        "jogos",
        [],
    )

    for group in groups:

        group_matches = group.get(
            "jogo",
            [],
        )

        for match in group_matches:

            home = match.get(
                "mandante",
                {},
            )

            away = match.get(
                "visitante",
                {},
            )

            venue, city, state = (
                parse_location(
                    match.get("local")
                )
            )

            matches.append(
                {
                    "season": CBF_SEASON,
                    "round": int(
                        match["rodada"]
                    ),
                    "match_id": int(
                        match["id_jogo"]
                    ),
                    "match_number": int(
                        match["num_jogo"]
                    ),
                    "group": match.get(
                        "grupo"
                    ),
                    "date": parse_match_date(
                        match.get("data")
                    ),
                    "time": parse_match_time(
                        match.get("hora")
                    ),
                    "home_team_id": int(
                        home["id"]
                    ),
                    "home_team": home.get(
                        "nome"
                    ),
                    "home_goals": (
                        parse_optional_int(
                            home.get("gols")
                        )
                    ),
                    "away_team_id": int(
                        away["id"]
                    ),
                    "away_team": away.get(
                        "nome"
                    ),
                    "away_goals": (
                        parse_optional_int(
                            away.get("gols")
                        )
                    ),
                    "venue": venue,
                    "city": city,
                    "state": state,
                    "championship": match.get(
                        "campeonato"
                    ),
                }
            )

    return matches


def fetch_all_matches(
    delay: float = 0.25,
) -> list[dict[str, Any]]:
    """Busca e normaliza as 38 rodadas do Brasileirão."""

    all_matches: list[
        dict[str, Any]
    ] = []

    session = create_session()

    try:

        for round_number in range(
            1,
            TOTAL_ROUNDS + 1,
        ):

            print(
                f"[INFO] Coletando rodada "
                f"{round_number}/{TOTAL_ROUNDS}..."
            )

            data = fetch_round(
                round_number,
                session=session,
            )

            matches = parse_round_matches(
                data
            )

            all_matches.extend(
                matches
            )

            print(
                f"[SUCCESS] Rodada "
                f"{round_number}: "
                f"{len(matches)} jogos."
            )

            if (
                delay > 0
                and round_number < TOTAL_ROUNDS
            ):
                time.sleep(delay)

    finally:
        session.close()

    return all_matches


def save_matches_csv(
    matches: list[dict[str, Any]],
) -> Path:
    """Salva todos os jogos do campeonato em CSV."""

    output_file = (
        get_processed_data_dir()
        / "matches.csv"
    )

    dataframe = pd.DataFrame(
        matches
    )

    if not dataframe.empty:

        dataframe = dataframe.sort_values(
            by=[
                "round",
                "match_number",
            ]
        )

    dataframe.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    return output_file