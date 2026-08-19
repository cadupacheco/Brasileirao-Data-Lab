from __future__ import annotations

from brasileirao_data_lab.ml.model_comparison import (
    run_model_comparison,
)


def main() -> None:
    print(
        "⚽ Brasileirão Data Lab - Comparação de Modelos V0.6"
    )
    print(
        "[INFO] Candidatos: Regressão Logística, "
        "Random Forest e Gradient Boosting."
    )
    print(
        "[INFO] Seleção baseada somente na validação de 2025."
    )

    run_model_comparison()


if __name__ == "__main__":
    main()