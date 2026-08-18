from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Generator

from sqlalchemy import (
    Engine,
    create_engine,
    event,
)
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from brasileirao_data_lab.database.config import (
    get_database_url,
)


# =============================================================================
# Engine
# =============================================================================


def create_database_engine(
    database_url: str | None = None,
) -> Engine:
    """
    Cria uma engine SQLAlchemy.

    Se nenhuma URL for informada,
    utiliza a configuração padrão do projeto.
    """

    url = (
        database_url
        or get_database_url()
    )

    engine = create_engine(
        url,
    )

    # -------------------------------------------------------------------------
    # SQLite
    # -------------------------------------------------------------------------

    if url.startswith(
        "sqlite"
    ):

        @event.listens_for(
            engine,
            "connect",
        )
        def enable_sqlite_foreign_keys(
            dbapi_connection,
            connection_record,
        ) -> None:
            """
            Ativa validação de Foreign Keys
            no SQLite.
            """

            del connection_record

            cursor = (
                dbapi_connection.cursor()
            )

            cursor.execute(
                "PRAGMA foreign_keys=ON"
            )

            cursor.close()

    return engine


# =============================================================================
# Engine principal
# =============================================================================


engine = create_database_engine()


# =============================================================================
# Session factory
# =============================================================================


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def create_session_factory(
    database_engine: Engine,
) -> sessionmaker[Session]:
    """
    Cria uma fábrica de sessões
    para uma engine específica.
    """

    return sessionmaker(
        bind=database_engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


# =============================================================================
# Context manager
# =============================================================================


@contextmanager
def session_scope() -> Generator[
    Session,
    None,
    None,
]:
    """
    Abre uma sessão transacional.

    Commit automático quando tudo funciona.
    Rollback automático em caso de erro.
    """

    session = SessionLocal()

    try:

        yield session

        session.commit()

    except Exception:

        session.rollback()

        raise

    finally:

        session.close()