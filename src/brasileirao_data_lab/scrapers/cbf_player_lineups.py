from __future__ import annotations

import re
import time
import unicodedata
from collections import defaultdict
from typing import Any

import requests
import truststore


# =============================================================================
# Configuração
# =============================================================================

CBF_SEASON = 2026

CBF_CHAMPIONSHIP_ID = 1260611

TOTAL_ROUNDS = 38

CBF_MATCHES_URL = (
    "https://www.cbf.com.br/api/cbf/jogos/"
    "campeonato/{competition_id}/"
    "rodada/{round_number}/fase"
)

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

HEADERS = {
    "Accept": (
        "application/json, "
        "text/plain, */*"
    ),
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Referer": (
        "https://www.cbf.com.br/"
        "futebol-brasileiro/tabelas/"
        "campeonato-brasileiro/"
        "serie-a/2026"
    ),
}


# =============================================================================
# SSL
# =============================================================================

truststore.inject_into_ssl()


# =============================================================================
# Sessão HTTP
# =============================================================================


def create_session() -> requests.Session:
    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    return session


# =============================================================================
# Normalização
# =============================================================================


def normalize_text(
    value: Any,
) -> str:
    if value is None:
        return ""

    text = str(
        value
    ).strip()

    normalized = unicodedata.normalize(
        "NFKD",
        text,
    )

    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    without_accents = (
        without_accents
        .casefold()
        .strip()
    )

    without_accents = re.sub(
        r"\s+",
        " ",
        without_accents,
    )

    return without_accents


def remove_shirt_number(
    value: Any,
) -> str:
    if value is None:
        return ""

    text = str(
        value
    ).strip()

    text = re.sub(
        r"^\s*\d+\s*-\s*",
        "",
        text,
    )

    return text.strip()


def parse_optional_int(
    value: Any,
) -> int | None:
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
# HTTP com retry
# =============================================================================


def fetch_round_payload(
    session: requests.Session,
    round_number: int,
    competition_id: int = CBF_CHAMPIONSHIP_ID,
) -> dict[str, Any]:
    if (
        round_number < 1
        or round_number > TOTAL_ROUNDS
    ):
        raise ValueError(
            "Rodada inválida: "
            f"{round_number}"
        )

    url = CBF_MATCHES_URL.format(
        competition_id=competition_id,
        round_number=round_number,
    )

    last_error: Exception | None = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):
        try:
            response = session.get(
                url,
                timeout=REQUEST_TIMEOUT,
            )

            if (
                response.status_code
                in RETRY_STATUS_CODES
            ):
                raise requests.HTTPError(
                    (
                        f"{response.status_code} "
                        f"Server Error para "
                        f"{url}"
                    ),
                    response=response,
                )

            response.raise_for_status()

            payload = response.json()

            if not isinstance(
                payload,
                dict,
            ):
                raise ValueError(
                    "Resposta da rodada "
                    "não é um objeto JSON."
                )

            return payload

        except (
            requests.RequestException,
            ValueError,
        ) as exc:
            last_error = exc

            is_last_attempt = (
                attempt
                == MAX_RETRIES
            )

            if is_last_attempt:
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
                f"[WARN] Rodada "
                f"{round_number}: "
                f"tentativa "
                f"{attempt}/"
                f"{MAX_RETRIES} "
                f"falhou: {exc}"
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
            f"Não foi possível carregar "
            f"a rodada {round_number} "
            f"após {MAX_RETRIES} "
            f"tentativas."
        )
    ) from last_error


# =============================================================================
# Partidas
# =============================================================================


def extract_matches(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    matches: list[
        dict[str, Any]
    ] = []

    groups = payload.get(
        "jogos",
        [],
    )

    if not isinstance(
        groups,
        list,
    ):
        return matches

    for group in groups:
        if not isinstance(
            group,
            dict,
        ):
            continue

        group_matches = group.get(
            "jogo",
            [],
        )

        if not isinstance(
            group_matches,
            list,
        ):
            continue

        for match in group_matches:
            if isinstance(
                match,
                dict,
            ):
                matches.append(
                    match
                )

    return matches


# =============================================================================
# Escalações
# =============================================================================


def normalize_lineup_player(
    athlete: dict[str, Any],
    team_id: int,
    team_name: str,
    round_number: int,
    match_id: int | None,
) -> dict[str, Any] | None:
    player_id = parse_optional_int(
        athlete.get(
            "id"
        )
    )

    if player_id is None:
        return None

    full_name = remove_shirt_number(
        athlete.get(
            "nome"
        )
    )

    nickname = remove_shirt_number(
        athlete.get(
            "apelido"
        )
    )

    if not full_name:
        return None

    return {
        "player_id":
            player_id,
        "full_name":
            full_name,
        "nickname":
            nickname or None,
        "team_id":
            team_id,
        "team_name":
            team_name,
        "round":
            round_number,
        "match_id":
            match_id,
    }


def extract_team_lineup(
    team: dict[str, Any],
    round_number: int,
    match_id: int | None,
) -> list[dict[str, Any]]:
    team_id = parse_optional_int(
        team.get(
            "id"
        )
    )

    if team_id is None:
        return []

    team_name = str(
        team.get(
            "nome"
        )
        or ""
    ).strip()

    athletes = team.get(
        "atletas",
        [],
    )

    if not isinstance(
        athletes,
        list,
    ):
        return []

    result: list[
        dict[str, Any]
    ] = []

    for athlete in athletes:
        if not isinstance(
            athlete,
            dict,
        ):
            continue

        normalized = (
            normalize_lineup_player(
                athlete=athlete,
                team_id=team_id,
                team_name=team_name,
                round_number=round_number,
                match_id=match_id,
            )
        )

        if normalized is not None:
            result.append(
                normalized
            )

    return result


def extract_round_lineups(
    payload: dict[str, Any],
    round_number: int,
) -> list[dict[str, Any]]:
    result: list[
        dict[str, Any]
    ] = []

    matches = extract_matches(
        payload
    )

    for match in matches:
        match_id = parse_optional_int(
            match.get(
                "id_jogo"
            )
        )

        home_team = match.get(
            "mandante",
            {},
        )

        away_team = match.get(
            "visitante",
            {},
        )

        if isinstance(
            home_team,
            dict,
        ):
            result.extend(
                extract_team_lineup(
                    team=home_team,
                    round_number=round_number,
                    match_id=match_id,
                )
            )

        if isinstance(
            away_team,
            dict,
        ):
            result.extend(
                extract_team_lineup(
                    team=away_team,
                    round_number=round_number,
                    match_id=match_id,
                )
            )

    return result


# =============================================================================
# Coleta do campeonato
# =============================================================================


def fetch_championship_lineups(
    competition_id: int = CBF_CHAMPIONSHIP_ID,
    total_rounds: int = TOTAL_ROUNDS,
    session: requests.Session | None = None,
) -> tuple[
    list[dict[str, Any]],
    list[int],
]:
    owns_session = (
        session is None
    )

    http_session = (
        session
        or create_session()
    )

    lineups: list[
        dict[str, Any]
    ] = []

    failed_rounds: list[int] = []

    try:
        for round_number in range(
            1,
            total_rounds + 1,
        ):
            print(
                f"[INFO] Escalações "
                f"rodada "
                f"{round_number:02d}/"
                f"{total_rounds}..."
            )

            try:
                payload = (
                    fetch_round_payload(
                        session=http_session,
                        round_number=(
                            round_number
                        ),
                        competition_id=(
                            competition_id
                        ),
                    )
                )

            except Exception as exc:
                print(
                    f"[WARN] Rodada "
                    f"{round_number} "
                    f"ignorada: {exc}"
                )

                failed_rounds.append(
                    round_number
                )

                continue

            round_lineups = (
                extract_round_lineups(
                    payload=payload,
                    round_number=(
                        round_number
                    ),
                )
            )

            lineups.extend(
                round_lineups
            )

            print(
                f"[INFO] "
                f"{len(round_lineups)} "
                f"registros de atletas."
            )

    finally:
        if owns_session:
            http_session.close()

    return (
        lineups,
        failed_rounds,
    )


# =============================================================================
# Índices
# =============================================================================


def build_lineup_indexes(
    lineups: list[dict[str, Any]],
) -> dict[
    str,
    dict[
        str,
        list[dict[str, Any]],
    ],
]:
    by_full_name: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(
        list
    )

    by_nickname: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(
        list
    )

    seen: set[
        tuple[
            int,
            int,
            str,
        ]
    ] = set()

    for player in lineups:
        player_id = int(
            player[
                "player_id"
            ]
        )

        team_id = int(
            player[
                "team_id"
            ]
        )

        full_name = str(
            player[
                "full_name"
            ]
        )

        full_key = normalize_text(
            full_name
        )

        dedupe_key = (
            player_id,
            team_id,
            full_key,
        )

        if (
            full_key
            and dedupe_key
            not in seen
        ):
            by_full_name[
                full_key
            ].append(
                player
            )

            seen.add(
                dedupe_key
            )

        nickname = player.get(
            "nickname"
        )

        nickname_key = normalize_text(
            nickname
        )

        if nickname_key:
            existing_ids = {
                (
                    int(
                        candidate[
                            "player_id"
                        ]
                    ),
                    int(
                        candidate[
                            "team_id"
                        ]
                    ),
                )
                for candidate
                in by_nickname[
                    nickname_key
                ]
            }

            current_identity = (
                player_id,
                team_id,
            )

            if (
                current_identity
                not in existing_ids
            ):
                by_nickname[
                    nickname_key
                ].append(
                    player
                )

    return {
        "full_name":
            dict(
                by_full_name
            ),
        "nickname":
            dict(
                by_nickname
            ),
    }


# =============================================================================
# Resolução
# =============================================================================


def unique_by_player_id(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unique: dict[
        int,
        dict[str, Any],
    ] = {}

    for candidate in candidates:
        player_id = int(
            candidate[
                "player_id"
            ]
        )

        if player_id not in unique:
            unique[
                player_id
            ] = candidate

    return list(
        unique.values()
    )


def choose_candidate(
    candidates: list[dict[str, Any]],
    team_id: int | None,
) -> dict[str, Any] | None:
    if not candidates:
        return None

    if team_id is not None:
        same_team = [
            candidate
            for candidate
            in candidates
            if int(
                candidate[
                    "team_id"
                ]
            )
            == int(
                team_id
            )
        ]

        same_team = (
            unique_by_player_id(
                same_team
            )
        )

        if len(
            same_team
        ) == 1:
            return same_team[0]

        if len(
            same_team
        ) > 1:
            return None

    unique_candidates = (
        unique_by_player_id(
            candidates
        )
    )

    if len(
        unique_candidates
    ) == 1:
        return (
            unique_candidates[0]
        )

    return None


def resolve_player_from_lineups(
    indexes: dict[
        str,
        dict[
            str,
            list[dict[str, Any]],
        ],
    ],
    full_name: str,
    team_id: int | None = None,
    nickname: str | None = None,
) -> dict[str, Any] | None:
    full_key = normalize_text(
        full_name
    )

    full_name_candidates = (
        indexes[
            "full_name"
        ].get(
            full_key,
            [],
        )
    )

    candidate = choose_candidate(
        candidates=(
            full_name_candidates
        ),
        team_id=team_id,
    )

    if candidate is not None:
        return candidate

    if nickname:
        nickname_key = (
            normalize_text(
                nickname
            )
        )

        nickname_candidates = (
            indexes[
                "nickname"
            ].get(
                nickname_key,
                [],
            )
        )

        candidate = (
            choose_candidate(
                candidates=(
                    nickname_candidates
                ),
                team_id=team_id,
            )
        )

        if candidate is not None:
            return candidate

    return None


# =============================================================================
# Construção pronta do resolver
# =============================================================================


def build_championship_lineup_resolver(
    competition_id: int = CBF_CHAMPIONSHIP_ID,
    total_rounds: int = TOTAL_ROUNDS,
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
    lineups, failed_rounds = (
        fetch_championship_lineups(
            competition_id=(
                competition_id
            ),
            total_rounds=(
                total_rounds
            ),
        )
    )

    indexes = (
        build_lineup_indexes(
            lineups
        )
    )

    unique_player_ids = {
        int(
            player[
                "player_id"
            ]
        )
        for player in lineups
    }

    metadata = {
        "lineup_records":
            len(
                lineups
            ),
        "unique_players":
            len(
                unique_player_ids
            ),
        "failed_rounds":
            failed_rounds,
    }

    return (
        indexes,
        metadata,
    )