from __future__ import annotations

import re
import time
import unicodedata
from typing import Any
from urllib.parse import urljoin

import requests
import truststore
from bs4 import BeautifulSoup
from bs4.element import Tag

from brasileirao_data_lab.scrapers.cbf_player_lineups import (
    build_championship_lineup_resolver,
    resolve_player_from_lineups,
)


# =============================================================================
# SSL
# =============================================================================

truststore.inject_into_ssl()


# =============================================================================
# Configurações da CBF
# =============================================================================

CBF_BASE_URL = (
    "https://www.cbf.com.br"
)

CBF_SEASON = 2026

CBF_CHAMPIONSHIP_ID = 1260611

CBF_TEAM_URL = (
    "https://www.cbf.com.br/"
    "futebol-brasileiro/times/"
    "campeonato-brasileiro/"
    "serie-a/{season}/{team_id}"
)

CBF_ATHLETES_API_URL = (
    "https://www.cbf.com.br/"
    "api/cbf/atletas/"
    "campeonato/{championship_id}/"
    "pagina/{page}"
)

CBF_PLAYER_PROFILE_URL = (
    "https://www.cbf.com.br/"
    "futebol-brasileiro/atletas/"
    "campeonato-brasileiro/"
    "serie-a/{season}/{player_id}"
)

HEADERS = {
    "Accept": (
        "application/json,"
        "text/html;q=0.9,"
        "*/*;q=0.8"
    ),
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 "
        "Safari/537.36"
    ),
}

REQUEST_TIMEOUT = 30

MAX_RETRIES = 4

RETRY_BASE_DELAY = 2.0

RETRY_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


# =============================================================================
# Cache da execução
# =============================================================================

_API_ATHLETES_CACHE: dict[
    tuple[int, int],
    list[dict[str, Any]],
] = {}

_LINEUP_RESOLVER_CACHE: dict[
    tuple[int, int],
    tuple[
        dict[
            str,
            dict[
                str,
                list[dict[str, Any]],
            ],
        ],
        dict[str, Any],
    ],
] = {}


# =============================================================================
# Cliente HTTP
# =============================================================================

def create_session() -> requests.Session:
    """
    Cria uma sessão HTTP reutilizável
    para acessar a CBF.
    """

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    return session


def request_with_retry(
    session: requests.Session,
    url: str,
    *,
    timeout: int = REQUEST_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    label: str = "requisição CBF",
) -> requests.Response:
    """
    Executa GET com retry para
    falhas temporárias.

    Erros permanentes como 404
    não são repetidos.
    """

    last_error: Exception | None = None

    for attempt in range(
        1,
        max_retries + 1,
    ):
        try:
            response = session.get(
                url,
                timeout=timeout,
            )

            if (
                response.status_code
                not in RETRY_STATUS_CODES
            ):
                response.raise_for_status()

                return response

            error = requests.HTTPError(
                (
                    f"{response.status_code} "
                    f"Server Error para {url}"
                ),
                response=response,
            )

            last_error = error

        except requests.RequestException as exc:
            last_error = exc

            response = getattr(
                exc,
                "response",
                None,
            )

            status_code = (
                response.status_code
                if response is not None
                else None
            )

            if (
                status_code is not None
                and status_code
                not in RETRY_STATUS_CODES
            ):
                raise

        if attempt >= max_retries:
            break

        wait_seconds = (
            RETRY_BASE_DELAY
            * (
                2
                ** (
                    attempt
                    - 1
                )
            )
        )

        print(
            f"[WARN] {label}: "
            f"tentativa "
            f"{attempt}/{max_retries} "
            f"falhou: {last_error}"
        )

        print(
            f"[INFO] Nova tentativa "
            f"em {wait_seconds:.0f}s..."
        )

        time.sleep(
            wait_seconds
        )

    raise RuntimeError(
        (
            f"{label} falhou após "
            f"{max_retries} tentativas."
        )
    ) from last_error


# =============================================================================
# Normalização
# =============================================================================

def normalize_text(
    value: str | None,
) -> str | None:
    """
    Remove espaços duplicados e
    normaliza textos opcionais.
    """

    if value is None:
        return None

    normalized = re.sub(
        r"\s+",
        " ",
        str(
            value
        ),
    ).strip()

    if not normalized:
        return None

    return normalized


def build_player_key(
    value: str,
) -> str:
    """
    Cria uma chave normalizada
    para relacionar atletas
    vindos de fontes diferentes
    dentro da própria CBF.
    """

    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    normalized = normalized.casefold()

    normalized = re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    )

    return normalized.strip(
        "-"
    )


def parse_optional_int(
    value: Any,
) -> int | None:
    """
    Converte valores opcionais
    para inteiro.
    """

    if value is None:
        return None

    text = str(
        value
    ).strip()

    if not text:
        return None

    try:
        return int(
            text
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


# =============================================================================
# URLs
# =============================================================================

def build_team_url(
    team_id: int,
    season: int = CBF_SEASON,
) -> str:
    """
    Monta a página oficial
    de um clube na competição.
    """

    if team_id <= 0:
        raise ValueError(
            "team_id deve ser maior que zero."
        )

    return CBF_TEAM_URL.format(
        season=season,
        team_id=team_id,
    )


def build_player_profile_url(
    player_id: int,
    season: int = CBF_SEASON,
) -> str:
    """
    Monta a página oficial
    de um atleta na CBF.
    """

    if player_id <= 0:
        raise ValueError(
            "player_id deve ser maior que zero."
        )

    return CBF_PLAYER_PROFILE_URL.format(
        season=season,
        player_id=player_id,
    )


# =============================================================================
# Página do clube
# =============================================================================

def fetch_team_players_page(
    team_id: int,
    season: int = CBF_SEASON,
    session: requests.Session | None = None,
) -> str:
    """
    Baixa o HTML da página pública
    do clube na CBF.
    """

    url = build_team_url(
        team_id=team_id,
        season=season,
    )

    owns_session = (
        session is None
    )

    http = (
        session
        or create_session()
    )

    try:
        response = request_with_retry(
            session=http,
            url=url,
            label=(
                f"página do clube "
                f"{team_id}"
            ),
        )

        return response.text

    finally:
        if owns_session:
            http.close()


def find_players_table(
    soup: BeautifulSoup,
) -> Tag:
    """
    Localiza a tabela de atletas
    presente na página do clube.
    """

    for table in soup.find_all(
        "table"
    ):
        headers = [
            header.get_text(
                " ",
                strip=True,
            )
            for header
            in table.find_all(
                "th"
            )
        ]

        normalized_headers = [
            header.casefold()
            for header
            in headers
        ]

        has_name = any(
            "nome" in header
            for header
            in normalized_headers
        )

        has_nickname = any(
            "apelido" in header
            for header
            in normalized_headers
        )

        has_current_club = any(
            "clube atual" in header
            for header
            in normalized_headers
        )

        if (
            has_name
            and has_nickname
            and has_current_club
        ):
            return table

    raise ValueError(
        "Tabela de atletas não encontrada "
        "na página da CBF."
    )


def parse_team_players(
    html: str,
    team_id: int,
    season: int = CBF_SEASON,
) -> list[dict[str, Any]]:
    """
    Extrai os atletas relacionados
    ao clube na competição.

    Nesta etapa o ID ainda pode não
    estar disponível.
    """

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    table = find_players_table(
        soup
    )

    players: list[
        dict[str, Any]
    ] = []

    seen_players: set[
        str
    ] = set()

    rows = table.find_all(
        "tr"
    )[1:]

    for row in rows:
        cells = row.find_all(
            "td"
        )

        if len(cells) < 3:
            continue

        full_name = normalize_text(
            cells[
                0
            ].get_text(
                " ",
                strip=True,
            )
        )

        nickname = normalize_text(
            cells[
                1
            ].get_text(
                " ",
                strip=True,
            )
        )

        current_club = normalize_text(
            cells[
                2
            ].get_text(
                " ",
                strip=True,
            )
        )

        if full_name is None:
            continue

        player_key = build_player_key(
            full_name
        )

        if not player_key:
            continue

        if (
            player_key
            in seen_players
        ):
            continue

        seen_players.add(
            player_key
        )

        players.append(
            {
                "season": season,
                "registration_team_id": (
                    team_id
                ),
                "player_id": None,
                "player_key": player_key,
                "full_name": full_name,
                "nickname": nickname,
                "listed_current_club": (
                    current_club
                ),
                "api_club_id": None,
                "api_club_name": None,
                "api_club_full_name": None,
                "api_club_state": None,
                "club_badge_url": None,
                "profile_url": None,
                "resolution_source": None,
            }
        )

    if not players:
        raise ValueError(
            "Nenhum atleta válido foi "
            "extraído da página da CBF."
        )

    return players


def fetch_team_players(
    team_id: int,
    season: int = CBF_SEASON,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """
    Busca apenas a relação de atletas
    encontrada na página de um clube.
    """

    owns_session = (
        session is None
    )

    http = (
        session
        or create_session()
    )

    try:
        html = (
            fetch_team_players_page(
                team_id=team_id,
                season=season,
                session=http,
            )
        )

        return parse_team_players(
            html=html,
            team_id=team_id,
            season=season,
        )

    finally:
        if owns_session:
            http.close()


# =============================================================================
# API oficial de atletas
# =============================================================================

def fetch_athletes_api_page(
    page: int,
    championship_id: int = CBF_CHAMPIONSHIP_ID,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    Busca uma página da API
    oficial de atletas da CBF.
    """

    if page <= 0:
        raise ValueError(
            "page deve ser maior que zero."
        )

    url = CBF_ATHLETES_API_URL.format(
        championship_id=championship_id,
        page=page,
    )

    owns_session = (
        session is None
    )

    http = (
        session
        or create_session()
    )

    try:
        response = request_with_retry(
            session=http,
            url=url,
            label=(
                f"API de atletas "
                f"página {page}"
            ),
        )

        payload = response.json()

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError(
                "Resposta inesperada da "
                "API de atletas."
            )

        return payload

    finally:
        if owns_session:
            http.close()


def get_api_total_pages(
    payload: dict[str, Any],
) -> int:
    """
    Obtém o total de páginas
    informado pela CBF.
    """

    meta = payload.get(
        "meta"
    )

    if (
        not isinstance(
            meta,
            list,
        )
        or not meta
        or not isinstance(
            meta[0],
            dict,
        )
    ):
        raise ValueError(
            "Metadata da API de atletas "
            "não encontrada."
        )

    total = parse_optional_int(
        meta[
            0
        ].get(
            "total"
        )
    )

    if (
        total is None
        or total <= 0
    ):
        raise ValueError(
            "Total de páginas inválido "
            "na API de atletas."
        )

    return total


def get_api_total_athletes(
    payload: dict[str, Any],
) -> int:
    """
    Obtém a quantidade total de atletas
    informada pela API.
    """

    meta = payload.get(
        "meta"
    )

    if (
        not isinstance(
            meta,
            list,
        )
        or not meta
        or not isinstance(
            meta[0],
            dict,
        )
    ):
        raise ValueError(
            "Metadata da API de atletas "
            "não encontrada."
        )

    total = parse_optional_int(
        meta[
            0
        ].get(
            "total_atletas"
        )
    )

    if total is None:
        raise ValueError(
            "Quantidade total de atletas "
            "não encontrada."
        )

    return total


def normalize_api_athlete(
    athlete: dict[str, Any],
    season: int = CBF_SEASON,
) -> dict[str, Any]:
    """
    Normaliza um atleta retornado
    pela API da CBF.

    CPF retornado pela API é
    deliberadamente descartado.
    """

    player_id = parse_optional_int(
        athlete.get(
            "atleta_id"
        )
    )

    full_name = normalize_text(
        athlete.get(
            "atleta_nome"
        )
    )

    if (
        player_id is None
        or full_name is None
    ):
        raise ValueError(
            "Atleta retornado pela API "
            "sem ID ou nome."
        )

    api_club_id = parse_optional_int(
        athlete.get(
            "clube_id"
        )
        or athlete.get(
            "Codigo_Clube"
        )
    )

    api_club_name = normalize_text(
        athlete.get(
            "clube_nome_popular"
        )
    )

    api_club_full_name = normalize_text(
        athlete.get(
            "clube_nome_completo"
        )
    )

    api_club_state = normalize_text(
        athlete.get(
            "clube_uf"
        )
    )

    club_badge_url = normalize_text(
        athlete.get(
            "clube_escudo"
        )
    )

    return {
        "season": season,
        "player_id": player_id,
        "player_key": build_player_key(
            full_name
        ),
        "full_name": full_name,
        "nickname": normalize_text(
            athlete.get(
                "atleta_apelido"
            )
        ),
        "api_club_id": api_club_id,
        "api_club_name": api_club_name,
        "api_club_full_name": (
            api_club_full_name
        ),
        "api_club_state": (
            api_club_state
        ),
        "club_badge_url": (
            club_badge_url
        ),
        "profile_url": (
            build_player_profile_url(
                player_id=player_id,
                season=season,
            )
        ),
    }


def parse_api_athletes(
    payload: dict[str, Any],
    season: int = CBF_SEASON,
) -> list[dict[str, Any]]:
    """
    Normaliza os atletas de uma
    página da API.
    """

    raw_athletes = payload.get(
        "atletas",
        [],
    )

    if not isinstance(
        raw_athletes,
        list,
    ):
        raise ValueError(
            "Campo atletas possui "
            "formato inesperado."
        )

    result: list[
        dict[str, Any]
    ] = []

    for athlete in raw_athletes:
        if not isinstance(
            athlete,
            dict,
        ):
            continue

        try:
            normalized = (
                normalize_api_athlete(
                    athlete,
                    season=season,
                )
            )

        except ValueError:
            continue

        result.append(
            normalized
        )

    return result


def fetch_all_championship_athletes(
    season: int = CBF_SEASON,
    championship_id: int = CBF_CHAMPIONSHIP_ID,
    delay: float = 0.05,
) -> list[dict[str, Any]]:
    """
    Percorre todas as páginas da API
    e retorna todos os atletas da
    competição.
    """

    session = create_session()

    try:
        first_payload = (
            fetch_athletes_api_page(
                page=1,
                championship_id=(
                    championship_id
                ),
                session=session,
            )
        )

        total_pages = (
            get_api_total_pages(
                first_payload
            )
        )

        expected_total = (
            get_api_total_athletes(
                first_payload
            )
        )

        athletes = (
            parse_api_athletes(
                first_payload,
                season=season,
            )
        )

        for page in range(
            2,
            total_pages + 1,
        ):
            if delay > 0:
                time.sleep(
                    delay
                )

            payload = (
                fetch_athletes_api_page(
                    page=page,
                    championship_id=(
                        championship_id
                    ),
                    session=session,
                )
            )

            athletes.extend(
                parse_api_athletes(
                    payload,
                    season=season,
                )
            )

        unique: dict[
            int,
            dict[str, Any],
        ] = {}

        for athlete in athletes:
            unique[
                int(
                    athlete[
                        "player_id"
                    ]
                )
            ] = athlete

        result = list(
            unique.values()
        )

        if (
            len(result)
            != expected_total
        ):
            raise ValueError(
                "Quantidade de atletas "
                "diferente do esperado. "
                f"Esperado: {expected_total}. "
                f"Obtido: {len(result)}."
            )

        return result

    finally:
        session.close()


def get_cached_championship_athletes(
    season: int = CBF_SEASON,
    championship_id: int = CBF_CHAMPIONSHIP_ID,
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    """
    Retorna a lista de atletas
    reutilizando o mesmo snapshot
    durante a execução atual.
    """

    cache_key = (
        season,
        championship_id,
    )

    if (
        force_refresh
        or cache_key
        not in _API_ATHLETES_CACHE
    ):
        print(
            "[INFO] Carregando índice "
            "geral de atletas da CBF..."
        )

        athletes = (
            fetch_all_championship_athletes(
                season=season,
                championship_id=(
                    championship_id
                ),
            )
        )

        _API_ATHLETES_CACHE[
            cache_key
        ] = athletes

        print(
            f"[SUCCESS] Índice da API: "
            f"{len(athletes)} atletas."
        )

    else:
        print(
            "[INFO] Reutilizando índice "
            "de atletas da CBF em cache."
        )

    return (
        _API_ATHLETES_CACHE[
            cache_key
        ]
    )


# =============================================================================
# Resolução pela API
# =============================================================================

def build_api_athlete_index(
    athletes: list[dict[str, Any]],
) -> dict[
    str,
    list[dict[str, Any]],
]:
    """
    Cria índice por nome normalizado.
    """

    index: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for athlete in athletes:
        key = athlete[
            "player_key"
        ]

        index.setdefault(
            key,
            [],
        ).append(
            athlete
        )

    return index


def choose_api_candidate(
    listed_player: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Escolhe o melhor registro da API
    para um atleta listado na página
    do clube.
    """

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[
            0
        ]

    listed_nickname = (
        build_player_key(
            listed_player[
                "nickname"
            ]
        )
        if listed_player.get(
            "nickname"
        )
        else None
    )

    if listed_nickname:
        nickname_matches = [
            athlete
            for athlete in candidates
            if (
                athlete.get(
                    "nickname"
                )
                and build_player_key(
                    athlete[
                        "nickname"
                    ]
                )
                == listed_nickname
            )
        ]

        if (
            len(
                nickname_matches
            )
            == 1
        ):
            return nickname_matches[
                0
            ]

    registration_team_id = (
        listed_player.get(
            "registration_team_id"
        )
    )

    team_matches = [
        athlete
        for athlete in candidates
        if athlete.get(
            "api_club_id"
        )
        == registration_team_id
    ]

    if (
        len(
            team_matches
        )
        == 1
    ):
        return team_matches[
            0
        ]

    return None


def resolve_team_players_from_api(
    listed_players: list[dict[str, Any]],
    api_athletes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Relaciona os atletas da página
    do clube com os IDs estruturados
    da API atual da CBF.
    """

    index = build_api_athlete_index(
        api_athletes
    )

    resolved: list[
        dict[str, Any]
    ] = []

    for listed_player in listed_players:
        key = listed_player[
            "player_key"
        ]

        candidates = index.get(
            key,
            [],
        )

        candidate = (
            choose_api_candidate(
                listed_player,
                candidates,
            )
        )

        player = dict(
            listed_player
        )

        if candidate is not None:
            player.update(
                {
                    "player_id": (
                        candidate[
                            "player_id"
                        ]
                    ),
                    "api_club_id": (
                        candidate[
                            "api_club_id"
                        ]
                    ),
                    "api_club_name": (
                        candidate[
                            "api_club_name"
                        ]
                    ),
                    "api_club_full_name": (
                        candidate[
                            "api_club_full_name"
                        ]
                    ),
                    "api_club_state": (
                        candidate[
                            "api_club_state"
                        ]
                    ),
                    "club_badge_url": (
                        candidate[
                            "club_badge_url"
                        ]
                    ),
                    "profile_url": (
                        candidate[
                            "profile_url"
                        ]
                    ),
                    "resolution_source": (
                        "athletes_api"
                    ),
                }
            )

        resolved.append(
            player
        )

    return resolved


# =============================================================================
# Resolução pelas escalações
# =============================================================================

def get_cached_lineup_resolver(
    season: int = CBF_SEASON,
    championship_id: int = CBF_CHAMPIONSHIP_ID,
    force_refresh: bool = False,
) -> tuple[
    dict[
        str,
        dict[
            str,
            list[dict[str, Any]],
        ],
    ],
    dict[str, Any],
]:
    """
    Constrói o índice das escalações
    apenas uma vez por execução.
    """

    cache_key = (
        season,
        championship_id,
    )

    if (
        force_refresh
        or cache_key
        not in _LINEUP_RESOLVER_CACHE
    ):
        print()
        print(
            "[INFO] Construindo fallback "
            "de atletas pelas escalações..."
        )

        indexes, metadata = (
            build_championship_lineup_resolver(
                competition_id=(
                    championship_id
                ),
            )
        )

        _LINEUP_RESOLVER_CACHE[
            cache_key
        ] = (
            indexes,
            metadata,
        )

        print(
            "[SUCCESS] Fallback de "
            "escalações construído."
        )

        print(
            f"[INFO] "
            f"{metadata['unique_players']} "
            f"atletas únicos encontrados "
            f"nas escalações."
        )

        failed_rounds = (
            metadata.get(
                "failed_rounds",
                [],
            )
        )

        if failed_rounds:
            print(
                "[WARN] Rodadas não "
                "carregadas: "
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
            "[INFO] Reutilizando fallback "
            "de escalações em cache."
        )

    return (
        _LINEUP_RESOLVER_CACHE[
            cache_key
        ]
    )


def resolve_unresolved_players_from_lineups(
    players: list[dict[str, Any]],
    lineup_indexes: dict[
        str,
        dict[
            str,
            list[dict[str, Any]],
        ],
    ],
    season: int = CBF_SEASON,
) -> list[dict[str, Any]]:
    """
    Utiliza escalações da competição
    como fallback para atletas que
    não existem mais na API atual.
    """

    result: list[
        dict[str, Any]
    ] = []

    for player in players:
        enriched = dict(
            player
        )

        if (
            enriched.get(
                "player_id"
            )
            is not None
        ):
            result.append(
                enriched
            )

            continue

        registration_team_id = (
            parse_optional_int(
                enriched.get(
                    "registration_team_id"
                )
            )
        )

        candidate = (
            resolve_player_from_lineups(
                indexes=(
                    lineup_indexes
                ),
                full_name=str(
                    enriched[
                        "full_name"
                    ]
                ),
                team_id=(
                    registration_team_id
                ),
                nickname=(
                    enriched.get(
                        "nickname"
                    )
                ),
            )
        )

        if candidate is None:
            result.append(
                enriched
            )

            continue

        player_id = int(
            candidate[
                "player_id"
            ]
        )

        enriched[
            "player_id"
        ] = player_id

        enriched[
            "profile_url"
        ] = (
            build_player_profile_url(
                player_id=player_id,
                season=season,
            )
        )

        enriched[
            "resolution_source"
        ] = "lineups"

        if (
            not enriched.get(
                "nickname"
            )
            and candidate.get(
                "nickname"
            )
        ):
            enriched[
                "nickname"
            ] = normalize_text(
                candidate.get(
                    "nickname"
                )
            )

        result.append(
            enriched
        )

    return result


# =============================================================================
# Resolução completa
# =============================================================================

def fetch_resolved_team_players(
    team_id: int,
    season: int = CBF_SEASON,
    championship_id: int = CBF_CHAMPIONSHIP_ID,
) -> list[dict[str, Any]]:
    """
    Resolve os jogadores do clube
    usando duas fontes:

    1. API atual de atletas;
    2. escalações históricas da
       própria competição.
    """

    session = create_session()

    try:
        listed_players = (
            fetch_team_players(
                team_id=team_id,
                season=season,
                session=session,
            )
        )

    finally:
        session.close()

    api_athletes = (
        get_cached_championship_athletes(
            season=season,
            championship_id=(
                championship_id
            ),
        )
    )

    players = (
        resolve_team_players_from_api(
            listed_players=(
                listed_players
            ),
            api_athletes=(
                api_athletes
            ),
        )
    )

    unresolved_before = [
        player
        for player in players
        if player.get(
            "player_id"
        )
        is None
    ]

    if not unresolved_before:
        return players

    print(
        f"[INFO] {len(unresolved_before)} "
        f"atleta(s) do clube {team_id} "
        f"não estão na API atual."
    )

    lineup_indexes, _ = (
        get_cached_lineup_resolver(
            season=season,
            championship_id=(
                championship_id
            ),
        )
    )

    players = (
        resolve_unresolved_players_from_lineups(
            players=players,
            lineup_indexes=(
                lineup_indexes
            ),
            season=season,
        )
    )

    unresolved_after = [
        player
        for player in players
        if player.get(
            "player_id"
        )
        is None
    ]

    recovered = (
        len(
            unresolved_before
        )
        - len(
            unresolved_after
        )
    )

    if recovered > 0:
        print(
            f"[SUCCESS] {recovered} "
            f"atleta(s) recuperado(s) "
            f"pelas escalações."
        )

    if unresolved_after:
        print(
            f"[WARN] "
            f"{len(unresolved_after)} "
            f"atleta(s) continuam "
            f"sem ID resolvido."
        )

        for player in (
            unresolved_after
        ):
            print(
                "       - "
                f"{player['full_name']}"
            )

    return players


# =============================================================================
# Perfil individual
# =============================================================================

def fetch_player_profile_page(
    player_id: int,
    season: int = CBF_SEASON,
    session: requests.Session | None = None,
) -> str:
    """
    Baixa o perfil individual
    de um atleta.

    Falhas temporárias recebem retry.
    Erros permanentes como 404 são
    propagados imediatamente.
    """

    url = build_player_profile_url(
        player_id=player_id,
        season=season,
    )

    owns_session = (
        session is None
    )

    http = (
        session
        or create_session()
    )

    try:
        response = request_with_retry(
            session=http,
            url=url,
            label=(
                f"perfil do atleta "
                f"{player_id}"
            ),
        )

        return response.text

    finally:
        if owns_session:
            http.close()


def extract_regex_group(
    pattern: str,
    text: str,
) -> str | None:
    """
    Retorna o primeiro grupo de uma
    expressão regular.
    """

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    return normalize_text(
        match.group(
            1
        )
    )


def parse_player_profile(
    html: str,
    player_id: int,
    season: int = CBF_SEASON,
) -> dict[str, Any]:
    """
    Extrai estatísticas básicas
    exibidas no perfil público
    do atleta na CBF.
    """

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    text = normalize_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    if text is None:
        raise ValueError(
            "Perfil do atleta vazio."
        )

    birth_date = extract_regex_group(
        r"Nascimento\s+"
        r"(\d{2}/\d{2}/\d{4})",
        text,
    )

    age_text = extract_regex_group(
        r"Idade\s+(\d{1,3})",
        text,
    )

    current_club = extract_regex_group(
        r"Clube atual\s+(.+?)\s+Nascimento",
        text,
    )

    stats_match = re.search(
        r"(\d+)\s+Partidas\s+"
        r"(\d+)\s+Gol(?:s)?\s+"
        r"(\d+)\s+Amarelo(?:s)?\s+"
        r"(\d+)\s+Vermelho(?:s)?",
        text,
        flags=re.IGNORECASE,
    )

    if stats_match is None:
        raise ValueError(
            "Estatísticas principais "
            "não encontradas no perfil "
            f"do atleta {player_id}."
        )

    matches = int(
        stats_match.group(
            1
        )
    )

    goals = int(
        stats_match.group(
            2
        )
    )

    yellow_cards = int(
        stats_match.group(
            3
        )
    )

    red_cards = int(
        stats_match.group(
            4
        )
    )

    return {
        "season": season,
        "player_id": player_id,
        "birth_date": birth_date,
        "age": (
            int(
                age_text
            )
            if age_text
            else None
        ),
        "profile_current_club": (
            current_club
        ),
        "matches": matches,
        "goals": goals,
        "yellow_cards": (
            yellow_cards
        ),
        "red_cards": (
            red_cards
        ),
    }


def fetch_player_profile_stats(
    player_id: int,
    season: int = CBF_SEASON,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    Busca e normaliza as estatísticas
    públicas de um atleta.
    """

    html = fetch_player_profile_page(
        player_id=player_id,
        season=season,
        session=session,
    )

    return parse_player_profile(
        html=html,
        player_id=player_id,
        season=season,
    )


# =============================================================================
# Pipeline completa de um clube
# =============================================================================

def fetch_team_players_with_stats(
    team_id: int,
    season: int = CBF_SEASON,
    profile_delay: float = 0.10,
) -> list[dict[str, Any]]:
    """
    Pipeline completa:

    1. atletas associados ao clube;
    2. IDs pela API atual;
    3. fallback pelas escalações;
    4. perfis individuais;
    5. estatísticas básicas.

    Falhas individuais não derrubam
    o restante do elenco.
    """

    players = (
        fetch_resolved_team_players(
            team_id=team_id,
            season=season,
        )
    )

    session = create_session()

    try:
        result: list[
            dict[str, Any]
        ] = []

        for index, player in enumerate(
            players,
            start=1,
        ):
            enriched = dict(
                player
            )

            player_id = player.get(
                "player_id"
            )

            if player_id is None:
                enriched.update(
                    {
                        "birth_date": None,
                        "age": None,
                        "profile_current_club": None,
                        "matches": None,
                        "goals": None,
                        "yellow_cards": None,
                        "red_cards": None,
                    }
                )

                result.append(
                    enriched
                )

                continue

            try:
                stats = (
                    fetch_player_profile_stats(
                        player_id=int(
                            player_id
                        ),
                        season=season,
                        session=session,
                    )
                )

            except Exception as exc:
                print(
                    f"[WARN] Perfil de "
                    f"{player.get('nickname') or player['full_name']} "
                    f"ignorado: {exc}"
                )

                enriched.update(
                    {
                        "birth_date": None,
                        "age": None,
                        "profile_current_club": None,
                        "matches": None,
                        "goals": None,
                        "yellow_cards": None,
                        "red_cards": None,
                    }
                )

                result.append(
                    enriched
                )

                continue

            enriched.update(
                stats
            )

            result.append(
                enriched
            )

            if (
                profile_delay > 0
                and index < len(
                    players
                )
            ):
                time.sleep(
                    profile_delay
                )

        return result

    finally:
        session.close()