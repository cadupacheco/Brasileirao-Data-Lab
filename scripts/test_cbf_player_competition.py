from __future__ import annotations

import json
from typing import Any

import requests
from bs4 import BeautifulSoup

from brasileirao_data_lab.scrapers.cbf_players import (
    CBF_SEASON,
    create_session,
    fetch_player_profile_page,
)


DEFAULT_COMPETITION = (
    "Campeonato Brasileiro"
)

DEFAULT_CATEGORY = (
    "Série A"
)


# =============================================================================
# Payload Next.js
# =============================================================================

def extract_next_flight_text(
    html: str,
) -> str:
    """
    Extrai e decodifica os blocos
    self.__next_f.push utilizados
    pelo Next.js da CBF.
    """

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    chunks: list[str] = []

    prefix = (
        "self.__next_f.push("
    )

    for script in soup.find_all(
        "script"
    ):
        script_text = (
            script.string
            or script.get_text()
            or ""
        ).strip()

        if not script_text.startswith(
            prefix
        ):
            continue

        if not script_text.endswith(
            ")"
        ):
            continue

        payload_text = (
            script_text[
                len(prefix):-1
            ]
        )

        try:
            payload = json.loads(
                payload_text
            )

        except json.JSONDecodeError:
            continue

        if (
            not isinstance(
                payload,
                list,
            )
            or len(
                payload
            ) < 2
        ):
            continue

        content = payload[
            1
        ]

        if isinstance(
            content,
            str,
        ):
            chunks.append(
                content
            )

    if not chunks:
        raise ValueError(
            "Nenhum payload Next.js "
            "foi encontrado no perfil."
        )

    return "\n".join(
        chunks
    )


def extract_json_object_after_key(
    text: str,
    key: str,
) -> dict[str, Any]:
    """
    Localiza uma chave JSON
    e extrai o objeto associado.
    """

    marker = (
        f'"{key}":'
    )

    marker_position = (
        text.find(
            marker
        )
    )

    if marker_position < 0:
        raise ValueError(
            f"Chave {key!r} "
            "não encontrada no payload."
        )

    object_start = (
        text.find(
            "{",
            marker_position
            + len(
                marker
            ),
        )
    )

    if object_start < 0:
        raise ValueError(
            f"Objeto da chave "
            f"{key!r} não encontrado."
        )

    depth = 0

    in_string = False
    escaped = False

    object_end: int | None = (
        None
    )

    for position in range(
        object_start,
        len(
            text
        ),
    ):
        character = text[
            position
        ]

        if in_string:
            if escaped:
                escaped = False
                continue

            if character == "\\":
                escaped = True
                continue

            if character == '"':
                in_string = False

            continue

        if character == '"':
            in_string = True
            continue

        if character == "{":
            depth += 1
            continue

        if character == "}":
            depth -= 1

            if depth == 0:
                object_end = (
                    position + 1
                )
                break

    if object_end is None:
        raise ValueError(
            f"Objeto JSON da chave "
            f"{key!r} está incompleto."
        )

    object_text = text[
        object_start:object_end
    ]

    try:
        parsed = json.loads(
            object_text
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Objeto JSON da chave "
            f"{key!r} não pôde ser "
            "decodificado."
        ) from exc

    if not isinstance(
        parsed,
        dict,
    ):
        raise ValueError(
            f"Valor de {key!r} "
            "não é um objeto."
        )

    return parsed


# =============================================================================
# Conversões
# =============================================================================

def parse_optional_int(
    value: Any,
) -> int:
    """
    Converte valores numéricos
    da CBF para inteiro.
    """

    if value is None:
        return 0

    text = str(
        value
    ).strip()

    if not text:
        return 0

    return int(
        text
    )


# =============================================================================
# Perfil
# =============================================================================

def extract_profile_payload(
    html: str,
) -> dict[str, Any]:
    """
    Extrai estatísticas anuais
    e partidas do atleta.
    """

    flight_text = (
        extract_next_flight_text(
            html
        )
    )

    year_stats = (
        extract_json_object_after_key(
            flight_text,
            "atleta_estatisticas",
        )
    )

    games = (
        extract_json_object_after_key(
            flight_text,
            "jogos",
        )
    )

    return {
        "year_stats": (
            year_stats
        ),
        "games": games,
    }


# =============================================================================
# Jogos por competição
# =============================================================================

def get_competition_games(
    profile_payload: dict[str, Any],
    competition: str = DEFAULT_COMPETITION,
    category: str = DEFAULT_CATEGORY,
) -> list[dict[str, Any]]:
    """
    Retorna somente partidas da
    competição/categoria informada.
    """

    games_root = (
        profile_payload.get(
            "games"
        )
    )

    if not isinstance(
        games_root,
        dict,
    ):
        raise ValueError(
            "Bloco de jogos inválido."
        )

    competition_root = (
        games_root.get(
            competition
        )
    )

    if competition_root is None:
        return []

    if not isinstance(
        competition_root,
        dict,
    ):
        raise ValueError(
            "Estrutura da competição "
            "é inválida."
        )

    raw_games = (
        competition_root.get(
            category,
            [],
        )
    )

    if raw_games is None:
        return []

    if not isinstance(
        raw_games,
        list,
    ):
        raise ValueError(
            "Lista de partidas "
            "possui formato inesperado."
        )

    return [
        game
        for game in raw_games
        if isinstance(
            game,
            dict,
        )
    ]


def game_has_team(
    game: dict[str, Any],
    team_id: int,
) -> bool:
    """
    Verifica se determinado clube
    participou da partida.
    """

    home_team_id = (
        parse_optional_int(
            game.get(
                "codigo_time_mandante"
            )
        )
    )

    away_team_id = (
        parse_optional_int(
            game.get(
                "codigo_time_visitante"
            )
        )
    )

    return (
        home_team_id == team_id
        or away_team_id == team_id
    )


def filter_games_by_team(
    games: list[dict[str, Any]],
    team_id: int,
) -> list[dict[str, Any]]:
    """
    Filtra partidas do atleta
    envolvendo somente o clube
    informado.
    """

    if team_id <= 0:
        raise ValueError(
            "team_id deve ser maior "
            "que zero."
        )

    return [
        game
        for game in games
        if game_has_team(
            game,
            team_id,
        )
    ]


# =============================================================================
# Estatísticas
# =============================================================================

def count_game_goals(
    game: dict[str, Any],
) -> int:
    """
    Conta gols atribuídos ao atleta
    naquela partida.
    """

    goals = game.get(
        "gols_atleta"
    )

    if not isinstance(
        goals,
        list,
    ):
        return 0

    return len(
        goals
    )


def build_competition_stats(
    games: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Calcula jogos, gols e cartões
    a partir da lista de partidas.
    """

    return {
        "matches": len(
            games
        ),
        "goals": sum(
            count_game_goals(
                game
            )
            for game in games
        ),
        "yellow_cards": sum(
            parse_optional_int(
                game.get(
                    "qtd_cartoes_amarelos"
                )
            )
            for game in games
        ),
        "red_cards": sum(
            parse_optional_int(
                game.get(
                    "qtd_cartoes_vermelhos"
                )
            )
            for game in games
        ),
    }


def build_year_stats(
    profile_payload: dict[str, Any],
) -> dict[str, int]:
    """
    Normaliza o resumo anual
    exibido pela CBF.
    """

    raw_stats = (
        profile_payload.get(
            "year_stats"
        )
    )

    if not isinstance(
        raw_stats,
        dict,
    ):
        raise ValueError(
            "Estatísticas anuais "
            "não encontradas."
        )

    return {
        "matches": (
            parse_optional_int(
                raw_stats.get(
                    "qtd_partidas"
                )
            )
        ),
        "goals": (
            parse_optional_int(
                raw_stats.get(
                    "qtd_gols"
                )
            )
        ),
        "yellow_cards": (
            parse_optional_int(
                raw_stats.get(
                    "qtd_cartoes_amarelos"
                )
            )
        ),
        "red_cards": (
            parse_optional_int(
                raw_stats.get(
                    "qtd_cartoes_vermelhos"
                )
            )
        ),
    }


# =============================================================================
# Normalização de partida
# =============================================================================

def normalize_game(
    game: dict[str, Any],
) -> dict[str, Any]:
    """
    Normaliza uma partida individual.
    """

    return {
        "match_id": (
            parse_optional_int(
                game.get(
                    "id_jogo"
                )
            )
        ),
        "home_team_id": (
            parse_optional_int(
                game.get(
                    "codigo_time_mandante"
                )
            )
        ),
        "home_team": (
            game.get(
                "nome_mandante"
            )
        ),
        "away_team_id": (
            parse_optional_int(
                game.get(
                    "codigo_time_visitante"
                )
            )
        ),
        "away_team": (
            game.get(
                "nome_visitante"
            )
        ),
        "home_goals": (
            parse_optional_int(
                game.get(
                    "placar_mandante"
                )
            )
        ),
        "away_goals": (
            parse_optional_int(
                game.get(
                    "placar_visitante"
                )
            )
        ),
        "date": (
            game.get(
                "data"
            )
        ),
        "time": (
            game.get(
                "hora"
            )
        ),
        "venue": (
            game.get(
                "local"
            )
        ),
        "goals": (
            count_game_goals(
                game
            )
        ),
        "yellow_cards": (
            parse_optional_int(
                game.get(
                    "qtd_cartoes_amarelos"
                )
            )
        ),
        "red_cards": (
            parse_optional_int(
                game.get(
                    "qtd_cartoes_vermelhos"
                )
            )
        ),
    }


# =============================================================================
# Parser de estatísticas
# =============================================================================

def parse_player_competition_stats(
    html: str,
    player_id: int,
    season: int = CBF_SEASON,
    competition: str = DEFAULT_COMPETITION,
    category: str = DEFAULT_CATEGORY,
    team_id: int | None = None,
) -> dict[str, Any]:
    """
    Extrai estatísticas específicas
    da competição.

    Quando team_id é informado,
    calcula também estatísticas
    específicas daquele clube.
    """

    profile_payload = (
        extract_profile_payload(
            html
        )
    )

    competition_games = (
        get_competition_games(
            profile_payload,
            competition=competition,
            category=category,
        )
    )

    competition_stats = (
        build_competition_stats(
            competition_games
        )
    )

    if team_id is None:
        team_games = list(
            competition_games
        )
    else:
        team_games = (
            filter_games_by_team(
                competition_games,
                team_id=team_id,
            )
        )

    team_stats = (
        build_competition_stats(
            team_games
        )
    )

    year_stats = (
        build_year_stats(
            profile_payload
        )
    )

    return {
        "season": season,
        "player_id": player_id,
        "competition": competition,
        "category": category,
        "team_id": team_id,

        "matches": (
            team_stats[
                "matches"
            ]
        ),
        "goals": (
            team_stats[
                "goals"
            ]
        ),
        "yellow_cards": (
            team_stats[
                "yellow_cards"
            ]
        ),
        "red_cards": (
            team_stats[
                "red_cards"
            ]
        ),

        "competition_matches": (
            competition_stats[
                "matches"
            ]
        ),
        "competition_goals": (
            competition_stats[
                "goals"
            ]
        ),
        "competition_yellow_cards": (
            competition_stats[
                "yellow_cards"
            ]
        ),
        "competition_red_cards": (
            competition_stats[
                "red_cards"
            ]
        ),

        "year_matches": (
            year_stats[
                "matches"
            ]
        ),
        "year_goals": (
            year_stats[
                "goals"
            ]
        ),
        "year_yellow_cards": (
            year_stats[
                "yellow_cards"
            ]
        ),
        "year_red_cards": (
            year_stats[
                "red_cards"
            ]
        ),

        "games": [
            normalize_game(
                game
            )
            for game in team_games
        ],

        "competition_games": [
            normalize_game(
                game
            )
            for game
            in competition_games
        ],
    }


def fetch_player_competition_stats(
    player_id: int,
    season: int = CBF_SEASON,
    competition: str = DEFAULT_COMPETITION,
    category: str = DEFAULT_CATEGORY,
    team_id: int | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    Busca o perfil e calcula
    estatísticas por competição
    e, opcionalmente, por clube.
    """

    html = (
        fetch_player_profile_page(
            player_id=player_id,
            season=season,
            session=session,
        )
    )

    return (
        parse_player_competition_stats(
            html=html,
            player_id=player_id,
            season=season,
            competition=competition,
            category=category,
            team_id=team_id,
        )
    )


def create_competition_session(
) -> requests.Session:
    """
    Cria sessão para auditorias
    de estatísticas.
    """

    return create_session()