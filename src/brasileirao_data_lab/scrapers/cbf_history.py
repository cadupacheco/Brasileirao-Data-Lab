from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests
import truststore


# =============================================================================
# Configuração
# =============================================================================

TOTAL_ROUNDS = 38

SEASON_COMPETITION_IDS: dict[int, int] = {
    2021: 12487,
    2022: 12518,
    2023: 12555,
    2024: 12584,
    2025: 12606,
    2026: 1260611,
}

CBF_MATCHES_URL = (
    "https://www.cbf.com.br/api/cbf/jogos/"
    "campeonato/{competition_id}/"
    "rodada/{round_number}/fase"
)

CBF_SEASON_PAGE_URL = (
    "https://www.cbf.com.br/"
    "futebol-brasileiro/tabelas/"
    "campeonato-brasileiro/serie-a/{season}"
)

REQUEST_TIMEOUT = 30
MAX_RETRIES = 4
RETRY_BASE_DELAY = 1.0

HEADERS = {
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
}


# =============================================================================
# SSL
# =============================================================================

truststore.inject_into_ssl()


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_ml_data_dir() -> Path:
    """Retorna a pasta reservada aos dados usados pela V0.6."""

    directory = (
        get_project_root()
        / "data"
        / "ml"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def get_history_output_file() -> Path:
    """Retorna o caminho do CSV histórico."""

    return (
        get_ml_data_dir()
        / "matches_history.csv"
    )


# =============================================================================
# Cliente HTTP
# =============================================================================


def create_session() -> requests.Session:
    """Cria uma sessão HTTP reutilizável."""

    session = requests.Session()
    session.headers.update(
        HEADERS
    )

    return session


def build_referer(
    season: int,
) -> str:
    """Monta a página oficial da temporada usada como Referer."""

    return CBF_SEASON_PAGE_URL.format(
        season=season
    )


# =============================================================================
# Conversões
# =============================================================================


def normalize_optional_text(
    value: Any,
) -> str | None:
    """Normaliza textos opcionais retornados pela CBF."""

    if value is None:
        return None

    clean_value = str(
        value
    ).strip()

    if not clean_value:
        return None

    undefined_values = {
        "a definir",
        "a confirmar",
        "não definido",
        "nao definido",
    }

    if (
        clean_value.casefold()
        in undefined_values
    ):
        return None

    return clean_value


def parse_optional_int(
    value: Any,
) -> int | None:
    """Converte valor opcional para inteiro."""

    clean_value = normalize_optional_text(
        value
    )

    if clean_value is None:
        return None

    return int(
        clean_value
    )


def parse_match_date(
    value: Any,
) -> str | None:
    """Converte DD/MM/YYYY para YYYY-MM-DD."""

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

    return (
        parsed_date
        .date()
        .isoformat()
    )


def parse_location(
    value: Any,
) -> tuple[
    str | None,
    str | None,
    str | None,
]:
    """Divide local em estádio, cidade e UF."""

    clean_value = normalize_optional_text(
        value
    )

    if clean_value is None:
        return (
            None,
            None,
            None,
        )

    parts = clean_value.rsplit(
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
        clean_value,
        None,
        None,
    )


# =============================================================================
# Resultado
# =============================================================================


def get_match_status(
    home_goals: int | None,
    away_goals: int | None,
) -> str:
    """Retorna played ou upcoming."""

    if (
        home_goals is not None
        and away_goals is not None
    ):
        return "played"

    return "upcoming"


def get_match_result(
    home_goals: int | None,
    away_goals: int | None,
) -> str | None:
    """
    Retorna HOME, DRAW ou AWAY.

    Jogos ainda não disputados retornam None.
    """

    if (
        home_goals is None
        or away_goals is None
    ):
        return None

    if home_goals > away_goals:
        return "HOME"

    if home_goals < away_goals:
        return "AWAY"

    return "DRAW"


# =============================================================================
# API da CBF
# =============================================================================


def fetch_round(
    season: int,
    round_number: int,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Busca uma rodada histórica com retry."""

    if (
        season
        not in SEASON_COMPETITION_IDS
    ):
        raise ValueError(
            f"Temporada não configurada: {season}."
        )

    if not 1 <= round_number <= TOTAL_ROUNDS:
        raise ValueError(
            "A rodada deve estar entre "
            f"1 e {TOTAL_ROUNDS}."
        )

    competition_id = (
        SEASON_COMPETITION_IDS[
            season
        ]
    )

    url = CBF_MATCHES_URL.format(
        competition_id=competition_id,
        round_number=round_number,
    )

    owns_session = (
        session is None
    )

    http = (
        session
        if session is not None
        else create_session()
    )

    try:
        for attempt in range(
            1,
            MAX_RETRIES + 1,
        ):
            try:
                response = http.get(
                    url,
                    timeout=REQUEST_TIMEOUT,
                    headers={
                        "Referer": build_referer(
                            season
                        ),
                    },
                )

                response.raise_for_status()

                return response.json()

            except (
                requests.RequestException,
                ValueError,
            ) as exc:
                if attempt >= MAX_RETRIES:
                    raise

                wait_seconds = (
                    RETRY_BASE_DELAY
                    * (2 ** (attempt - 1))
                )

                print(
                    "[WARN] Falha ao buscar "
                    f"{season} rodada "
                    f"{round_number}. "
                    f"Tentativa {attempt}/"
                    f"{MAX_RETRIES}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                print(
                    "[INFO] Nova tentativa em "
                    f"{wait_seconds:.1f}s..."
                )

                time.sleep(
                    wait_seconds
                )

    finally:
        if owns_session:
            http.close()

    raise RuntimeError(
        "Fluxo inesperado em fetch_round."
    )


# =============================================================================
# Parser
# =============================================================================


def parse_round_matches(
    season: int,
    data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Normaliza os jogos de uma rodada."""

    matches: list[
        dict[str, Any]
    ] = []

    groups = data.get(
        "jogos",
        [],
    )

    for group in groups:
        group_name = normalize_optional_text(
            group.get("grupo")
        )

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

            home_goals = (
                parse_optional_int(
                    home.get("gols")
                )
            )
            away_goals = (
                parse_optional_int(
                    away.get("gols")
                )
            )

            matches.append(
                {
                    "season": season,
                    "competition_id": (
                        SEASON_COMPETITION_IDS[
                            season
                        ]
                    ),
                    "round": int(
                        match["rodada"]
                    ),
                    "match_id": int(
                        match["id_jogo"]
                    ),
                    "match_number": (
                        parse_optional_int(
                            match.get(
                                "num_jogo"
                            )
                        )
                    ),
                    "group": (
                        normalize_optional_text(
                            match.get("grupo")
                        )
                        or group_name
                    ),
                    "date": (
                        parse_match_date(
                            match.get("data")
                        )
                    ),
                    "time": (
                        normalize_optional_text(
                            match.get("hora")
                        )
                    ),
                    "home_team_id": int(
                        home["id"]
                    ),
                    "home_team": (
                        normalize_optional_text(
                            home.get("nome")
                        )
                    ),
                    "home_goals": home_goals,
                    "away_team_id": int(
                        away["id"]
                    ),
                    "away_team": (
                        normalize_optional_text(
                            away.get("nome")
                        )
                    ),
                    "away_goals": away_goals,
                    "venue": venue,
                    "city": city,
                    "state": state,
                    "championship": (
                        normalize_optional_text(
                            match.get(
                                "campeonato"
                            )
                        )
                    ),
                    "status": (
                        get_match_status(
                            home_goals,
                            away_goals,
                        )
                    ),
                    "result": (
                        get_match_result(
                            home_goals,
                            away_goals,
                        )
                    ),
                }
            )

    return matches


# =============================================================================
# Coleta
# =============================================================================


def fetch_season_matches(
    season: int,
    delay: float = 0.20,
) -> list[dict[str, Any]]:
    """Busca as 38 rodadas de uma temporada."""

    if (
        season
        not in SEASON_COMPETITION_IDS
    ):
        raise ValueError(
            f"Temporada não configurada: {season}."
        )

    session = create_session()

    all_matches: list[
        dict[str, Any]
    ] = []

    try:
        for round_number in range(
            1,
            TOTAL_ROUNDS + 1,
        ):
            print(
                "[INFO] "
                f"{season} | rodada "
                f"{round_number:02d}/"
                f"{TOTAL_ROUNDS}"
            )

            data = fetch_round(
                season=season,
                round_number=round_number,
                session=session,
            )

            matches = (
                parse_round_matches(
                    season=season,
                    data=data,
                )
            )

            all_matches.extend(
                matches
            )

            print(
                "[SUCCESS] "
                f"{season} | rodada "
                f"{round_number:02d}: "
                f"{len(matches)} jogos"
            )

            if (
                delay > 0
                and round_number
                < TOTAL_ROUNDS
            ):
                time.sleep(
                    delay
                )

    finally:
        session.close()

    return all_matches


def fetch_history(
    seasons: Iterable[int] | None = None,
    delay: float = 0.20,
) -> list[dict[str, Any]]:
    """Coleta todas as temporadas configuradas."""

    selected_seasons = (
        tuple(seasons)
        if seasons is not None
        else tuple(
            SEASON_COMPETITION_IDS
        )
    )

    all_matches: list[
        dict[str, Any]
    ] = []

    for season in selected_seasons:
        print()
        print(
            "=" * 88
        )
        print(
            "[INFO] Coletando temporada "
            f"{season}"
        )
        print(
            "=" * 88
        )

        season_matches = (
            fetch_season_matches(
                season=season,
                delay=delay,
            )
        )

        validate_season_matches(
            season=season,
            matches=season_matches,
        )

        all_matches.extend(
            season_matches
        )

        print(
            "[SUCCESS] Temporada "
            f"{season}: "
            f"{len(season_matches)} jogos"
        )

    return all_matches


# =============================================================================
# Validação
# =============================================================================


def validate_season_matches(
    season: int,
    matches: list[dict[str, Any]],
) -> None:
    """Valida a estrutura básica de uma temporada."""

    expected_matches = 380

    if len(matches) != expected_matches:
        raise ValueError(
            f"{season}: esperado "
            f"{expected_matches} jogos, "
            f"recebidos {len(matches)}."
        )

    match_ids = [
        match["match_id"]
        for match in matches
    ]

    if (
        len(match_ids)
        != len(set(match_ids))
    ):
        raise ValueError(
            f"{season}: existem match_id duplicados."
        )

    missing_teams = [
        match
        for match in matches
        if (
            match["home_team"] is None
            or match["away_team"] is None
        )
    ]

    if missing_teams:
        raise ValueError(
            f"{season}: existem jogos sem nome de clube."
        )


def validate_history_dataframe(
    dataframe: pd.DataFrame,
) -> None:
    """Valida o dataset histórico consolidado."""

    if dataframe.empty:
        raise ValueError(
            "Dataset histórico vazio."
        )

    duplicate_ids = (
        dataframe[
            "match_id"
        ]
        .duplicated()
        .sum()
    )

    if duplicate_ids:
        raise ValueError(
            "Foram encontrados "
            f"{duplicate_ids} match_id duplicados "
            "no histórico."
        )

    if dataframe[
        "season"
    ].isna().any():
        raise ValueError(
            "Existem partidas sem temporada."
        )

    if dataframe[
        "round"
    ].isna().any():
        raise ValueError(
            "Existem partidas sem rodada."
        )


# =============================================================================
# Persistência
# =============================================================================


def build_history_dataframe(
    matches: list[dict[str, Any]],
) -> pd.DataFrame:
    """Cria e ordena o DataFrame histórico."""

    dataframe = pd.DataFrame(
        matches
    )

    if dataframe.empty:
        return dataframe

    dataframe = dataframe.sort_values(
        by=[
            "season",
            "round",
            "match_number",
            "match_id",
        ],
        na_position="last",
    ).reset_index(
        drop=True
    )

    validate_history_dataframe(
        dataframe
    )

    return dataframe


def save_history_csv(
    matches: list[dict[str, Any]],
) -> Path:
    """Salva o histórico consolidado em CSV."""

    dataframe = (
        build_history_dataframe(
            matches
        )
    )

    output_file = (
        get_history_output_file()
    )

    dataframe.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    return output_file


# =============================================================================
# Resumo
# =============================================================================


def print_history_summary(
    matches: list[dict[str, Any]],
) -> None:
    """Imprime o resumo da coleta."""

    dataframe = (
        build_history_dataframe(
            matches
        )
    )

    print()
    print(
        "=" * 88
    )
    print(
        "[SUMMARY] Dataset histórico"
    )
    print(
        "=" * 88
    )

    for season in sorted(
        dataframe[
            "season"
        ].unique()
    ):
        season_data = dataframe[
            dataframe[
                "season"
            ] == season
        ]

        played = int(
            (
                season_data[
                    "status"
                ] == "played"
            ).sum()
        )

        upcoming = int(
            (
                season_data[
                    "status"
                ] == "upcoming"
            ).sum()
        )

        print(
            f"{int(season)}: "
            f"{len(season_data)} jogos | "
            f"jogados={played} | "
            f"futuros={upcoming}"
        )

    print(
        "-" * 88
    )
    print(
        f"TOTAL: {len(dataframe)} jogos"
    )

    played_total = int(
        (
            dataframe[
                "status"
            ] == "played"
        ).sum()
    )

    upcoming_total = int(
        (
            dataframe[
                "status"
            ] == "upcoming"
        ).sum()
    )

    print(
        f"JOGADOS: {played_total}"
    )
    print(
        f"FUTUROS: {upcoming_total}"
    )