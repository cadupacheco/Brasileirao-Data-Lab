from __future__ import annotations

from brasileirao_data_lab.pipelines.update_detector import (
    CURRENT_SEASON,
    load_saved_history,
)
from brasileirao_data_lab.update_metadata import (
    build_update_metadata,
    save_update_metadata,
)


def main() -> None:
    """
    Gera o metadata público da versão atual
    dos dados do Brasileirão.
    """

    print()
    print("📡 Brasileirão Data Lab")
    print("📝 Gerando metadata da atualização")
    print("=" * 72)
    print()

    matches = load_saved_history()

    metadata = build_update_metadata(
        matches=matches,
        season=CURRENT_SEASON,
    )

    target = save_update_metadata(
        metadata
    )

    print(
        f"[SUCCESS] Metadata salvo em: "
        f"{target}"
    )

    print(
        f"[INFO] Temporada: "
        f"{metadata.season}"
    )

    print(
        f"[INFO] Fonte: "
        f"{metadata.source}"
    )

    print(
        f"[INFO] Snapshot: "
        f"{metadata.last_sync_at_utc}"
    )

    print(
        f"[INFO] Jogos disputados: "
        f"{metadata.played_matches}"
    )

    print(
        f"[INFO] Jogos futuros: "
        f"{metadata.future_matches}"
    )

    print()
    print(
        "[SUCCESS] Metadata da V0.7 "
        "gerado com sucesso."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()