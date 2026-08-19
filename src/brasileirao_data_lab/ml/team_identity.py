from __future__ import annotations

import unicodedata


# =============================================================================
# Identidade canônica dos clubes
# =============================================================================

TEAM_NAME_ALIASES: dict[str, str] = {
    "America": "america_mg",
    "América": "america_mg",
    "Athletico Paranaense": "athletico_paranaense",
    "Atlético": "atletico_goianiense",
    "Atlético Goianiense Saf": "atletico_goianiense",
    "Atlético Mineiro": "atletico_mineiro",
    "Avaí": "avai",
    "Bahia": "bahia",
    "Botafogo": "botafogo",
    "Ceará": "ceara",
    "Chapecoense": "chapecoense",
    "Corinthians": "corinthians",
    "Coritiba": "coritiba",
    "Coritiba SAF": "coritiba",
    "Criciúma": "criciuma",
    "Cruzeiro": "cruzeiro",
    "Cuiabá": "cuiaba",
    "Esporte Clube Bahia": "bahia",
    "Flamengo": "flamengo",
    "Fluminense": "fluminense",
    "Fortaleza Esporte Clube": "fortaleza",
    "Fortaleza SAF": "fortaleza",
    "Goiás": "goias",
    "Grêmio": "gremio",
    "Internacional": "internacional",
    "Juventude": "juventude",
    "Mirassol": "mirassol",
    "Palmeiras": "palmeiras",
    "Red Bull Bragantino": "red_bull_bragantino",
    "Remo": "remo",
    "Santos FC": "santos",
    "São Paulo": "sao_paulo",
    "Sport Recife": "sport_recife",
    "Vasco da Gama Saf": "vasco_da_gama",
    "Vitória": "vitoria",
}


# =============================================================================
# Normalização
# =============================================================================


def fallback_slug(
    team_name: str,
) -> str:
    """
    Cria uma chave estável para nomes ainda não conhecidos.

    O fallback existe para o coletor não quebrar caso uma nova equipe apareça,
    mas novos nomes devem ser revisados e adicionados ao mapa explícito.
    """

    normalized = unicodedata.normalize(
        "NFKD",
        team_name,
    )

    ascii_name = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    clean = (
        ascii_name
        .casefold()
        .replace("-", " ")
    )

    parts = [
        part
        for part in clean.split()
        if part
    ]

    return "_".join(
        parts
    )


def canonical_team_key(
    team_name: str,
) -> str:
    """Retorna a identidade canônica de um clube."""

    clean_name = str(
        team_name
    ).strip()

    if not clean_name:
        raise ValueError(
            "Nome do clube não pode ser vazio."
        )

    explicit = TEAM_NAME_ALIASES.get(
        clean_name
    )

    if explicit is not None:
        return explicit

    return fallback_slug(
        clean_name
    )


def is_known_team_name(
    team_name: str,
) -> bool:
    """Indica se o nome bruto já foi revisado manualmente."""

    clean_name = str(
        team_name
    ).strip()

    return (
        clean_name
        in TEAM_NAME_ALIASES
    )