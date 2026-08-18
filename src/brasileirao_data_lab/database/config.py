from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a pasta raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_default_database_file() -> Path:
    """
    Retorna o caminho padrão do banco SQLite.
    """

    database_file = (
        get_project_root()
        / "data"
        / "brasileirao.db"
    )

    database_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return database_file


# =============================================================================
# Ambiente
# =============================================================================


def load_environment() -> None:
    """Carrega as variáveis do arquivo .env."""

    env_file = (
        get_project_root()
        / ".env"
    )

    if env_file.exists():

        load_dotenv(
            env_file
        )


# =============================================================================
# Database URL
# =============================================================================


def get_default_database_url() -> str:
    """
    Monta a URL padrão do SQLite
    usando caminho absoluto.
    """

    database_file = (
        get_default_database_file()
        .resolve()
    )

    return (
        "sqlite:///"
        f"{database_file.as_posix()}"
    )


def get_database_url() -> str:
    """
    Retorna a URL utilizada pelo banco.

    Prioridade:

    1. DATABASE_URL do ambiente
    2. SQLite local em data/brasileirao.db
    """

    load_environment()

    configured_url = os.getenv(
        "DATABASE_URL"
    )

    if (
        configured_url
        and configured_url.strip()
    ):

        return configured_url.strip()

    return get_default_database_url()