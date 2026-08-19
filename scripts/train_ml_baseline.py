from __future__ import annotations

from brasileirao_data_lab.ml.baseline import (
    load_features,
    run_baseline,
)


def main() -> None:
    print(
        "⚽ Brasileirão Data Lab - Baseline ML V0.6"
    )
    print(
        "[INFO] Modelo: Regressão Logística multinomial"
    )
    print(
        "[INFO] Split temporal: treino até 2024, "
        "validação 2025, teste 2026."
    )

    dataframe = load_features()

    run_baseline(
        dataframe
    )


if __name__ == "__main__":
    main()