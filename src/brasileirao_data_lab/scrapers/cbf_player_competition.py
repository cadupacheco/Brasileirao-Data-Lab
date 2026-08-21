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


# =============================================================================
# Configuração
# =============================================================================

DEFAULT_COMPETITION = (
    "Campeonato Brasileiro"
)

DEFAULT_CATEGORY = (
    "Série A"
)


# =============================================================================
# Next.js payload
# =============================================================================

def extract_next_flight_text(
    html: str,
) -> str:
    """
    Extrai os blocos self.__next_f.push
    presentes nas páginas Next.js da CBF.
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
    Localiza uma chave JSON no payload
    e extrai o objeto associado utilizando
    balanceamento de chaves.
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
            f"Chave {key!r} não encontrada."
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
        result = json.loads(
            object_text
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Falha ao decodificar "
            f"o objeto {key!r}."
        ) from exc

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError(
            f"{key!r} não contém "
            "um objeto JSON."
        )

    return result


# =============================================================================
# Conversões
# =============================================================================

def parse_optional_int(
    value: Any,
) -> int:
    """
    Converte números da CBF
    para inteiro.

    Valores vazios representam zero
    nos campos estatísticos.
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
# Perfil do atleta
# =============================================================================

def extract_profile_payload(
    html: str,
) -> dict[str, Any]:
    """
    Extrai do perfil:

    - resumo estatístico anual
    - partidas separadas por competição
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
    Retorna somente as partidas
    da competição selecionada.

    Exemplo:

    Campeonato Brasileiro
    -> Série A
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
            "Lista de partidas inválida."
        )

    return [
        game
        for game in raw_games
        if isinstance(
            game,
            dict,
        )
    ]


# =============================================================================
# Filtro por clube
# =============================================================================

def game_has_team(
    game: dict[str, Any],
    team_id: int,
) -> bool:
    """
    Verifica se o clube informado
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
    Retorna somente partidas
    envolvendo determinado clube.
    """

    if team_id <= 0:
        raise ValueError(
            "team_id deve ser "
            "maior que zero."
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
    Conta os gols do atleta
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
    Calcula estatísticas utilizando
    diretamente as partidas.
    """

    matches = len(
        games
    )

    goals = sum(
        count_game_goals(
            game
        )
        for game in games
    )

    yellow_cards = sum(
        parse_optional_int(
            game.get(
                "qtd_cartoes_amarelos"
            )
        )
        for game in games
    )

    red_cards = sum(
        parse_optional_int(
            game.get(
                "qtd_cartoes_vermelhos"
            )
        )
        for game in games
    )

    return {
        "matches": matches,
        "goals": goals,
        "yellow_cards": (
            yellow_cards
        ),
        "red_cards": (
            red_cards
        ),
    }


def build_year_stats(
    profile_payload: dict[str, Any],
) -> dict[str, int]:
    """
    Normaliza o resumo anual
    exibido pela CBF.

    Esse resumo inclui outras
    competições e serve apenas
    para auditoria.
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
    Normaliza os campos úteis
    de uma partida do atleta.
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
# Parser principal
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
    Calcula estatísticas específicas
    de uma competição.

    Se team_id for informado,
    calcula somente partidas
    daquele clube.
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

    normalized_team_games = [
        normalize_game(
            game
        )
        for game in team_games
    ]

    normalized_competition_games = [
        normalize_game(
            game
        )
        for game
        in competition_games
    ]

    return {
        "season": season,
        "player_id": player_id,
        "competition": competition,
        "category": category,
        "team_id": team_id,

        # -------------------------------------------------------------
        # Clube selecionado
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # Competição completa
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # Ano completo
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # Jogos
        # -------------------------------------------------------------

        "games": (
            normalized_team_games
        ),

        "competition_games": (
            normalized_competition_games
        ),
    }


# =============================================================================
# Busca online
# =============================================================================

def fetch_player_competition_stats(
    player_id: int,
    season: int = CBF_SEASON,
    competition: str = DEFAULT_COMPETITION,
    category: str = DEFAULT_CATEGORY,
    team_id: int | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    Baixa o perfil do atleta
    e calcula estatísticas
    específicas da competição
    e do clube.
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


# =============================================================================
# Compatibilidade com auditoria anterior
# =============================================================================

def compare_year_and_competition_stats(
    stats: dict[str, Any],
) -> bool:
    """
    Compara o resumo anual da CBF
    com a competição completa.

    Mantido para compatibilidade
    com test_cbf_player_competition.py.
    """

    return (
        stats[
            "competition_matches"
        ]
        == stats[
            "year_matches"
        ]
        and stats[
            "competition_goals"
        ]
        == stats[
            "year_goals"
        ]
        and stats[
            "competition_yellow_cards"
        ]
        == stats[
            "year_yellow_cards"
        ]
        and stats[
            "competition_red_cards"
        ]
        == stats[
            "year_red_cards"
        ]
    )


# =============================================================================
# Sessão
# =============================================================================

def create_competition_session(
) -> requests.Session:
    """
    Cria uma sessão HTTP reutilizável
    para consultas dos atletas.
    """

    return create_session()