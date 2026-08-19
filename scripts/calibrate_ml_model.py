from __future__ import annotations

from brasileirao_data_lab.ml.calibration import (
    run_calibration_report,
)


def main() -> None:
    print(
        "⚽ Brasileirão Data Lab - Calibração de Probabilidades V0.6"
    )
    print(
        "[INFO] Modelo base: Random Forest."
    )
    print(
        "[INFO] Método: temperature scaling multiclasse."
    )
    print(
        "[INFO] Temperatura aprendida em 2025; "
        "2026 fica apenas como referência."
    )

    run_calibration_report()


if __name__ == "__main__":
    main()