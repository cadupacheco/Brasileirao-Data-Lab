from __future__ import annotations

from sqlalchemy import (
    Engine,
    inspect,
)

from brasileirao_data_lab.database.models import (
    Base,
)
from brasileirao_data_lab.database.session import (
    engine,
)


# =============================================================================
# Inicialização
# =============================================================================


def init_database(
    database_engine: Engine | None = None,
) -> list[str]:
    """
    Cria todas as tabelas registradas
    nos modelos SQLAlchemy.

    Retorna os nomes das tabelas criadas.
    """

    selected_engine = (
        database_engine
        or engine
    )

    Base.metadata.create_all(
        selected_engine
    )

    inspector = inspect(
        selected_engine
    )

    return sorted(
        inspector.get_table_names()
    )


# =============================================================================
# Terminal
# =============================================================================


def main() -> None:
    """Inicializa o banco do projeto."""

    print()
    print("⚽ Brasileirão Data Lab")
    print("🗄️ V0.3 - Database")
    print("=" * 70)

    print()
    print(
        "[INFO] Inicializando banco de dados..."
    )

    tables = init_database()

    print()
    print(
        "[SUCCESS] Banco inicializado."
    )

    print()
    print("Tabelas:")

    for table in tables:

        print(
            f"  - {table}"
        )

    print()
    print(
        f"[SUCCESS] "
        f"{len(tables)} tabelas disponíveis."
    )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()