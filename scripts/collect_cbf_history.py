from __future__ import annotations

from brasileirao_data_lab.scrapers.cbf_history import (
    fetch_history,
    print_history_summary,
    save_history_csv,
)


def main() -> None:
    print(
        "⚽ Brasileirão Data Lab - Coleta histórica V0.6"
    )
    print(
        "[INFO] Temporadas: 2021 a 2026"
    )
    print(
        "[INFO] O processo pode levar alguns minutos."
    )

    matches = fetch_history()

    print_history_summary(
        matches
    )

    output_file = save_history_csv(
        matches
    )

    print()
    print(
        "[SUCCESS] Histórico salvo em:"
    )
    print(
        output_file
    )


if __name__ == "__main__":
    main()