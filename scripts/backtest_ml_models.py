from __future__ import annotations

from brasileirao_data_lab.ml.backtest import (
    run_backtest_report,
)


def main() -> None:
    print(
        "⚽ Brasileirão Data Lab - Backtest de Modelos V0.6"
    )
    print(
        "[INFO] Validações: 2023, 2024 e 2025."
    )
    print(
        "[INFO] O vencedor é escolhido pela média de log loss."
    )
    print(
        "[INFO] 2026 fica apenas como referência."
    )

    run_backtest_report()


if __name__ == "__main__":
    main()