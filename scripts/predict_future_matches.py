from __future__ import annotations

from brasileirao_data_lab.ml.baseline import (
    load_features,
)
from brasileirao_data_lab.ml.features import (
    load_history_dataframe,
)
from brasileirao_data_lab.ml.predictions import (
    generate_future_predictions,
    print_prediction_summary,
    save_predictions,
)


def main() -> None:
    print(
        "⚽ Brasileirão Data Lab - Previsões Futuras V0.6"
    )
    print(
        "[INFO] Modelo final: Random Forest."
    )
    print(
        "[INFO] Treino: todas as partidas já disputadas disponíveis."
    )
    print(
        "[INFO] Saída: probabilidades HOME / DRAW / AWAY."
    )

    feature_dataset = load_features()

    history = load_history_dataframe()

    predictions = generate_future_predictions(
        feature_dataset=feature_dataset,
        history=history,
    )

    print_prediction_summary(
        predictions
    )

    output_file = save_predictions(
        predictions
    )

    print()
    print(
        "[SUCCESS] Previsões salvas em:"
    )
    print(
        output_file
    )


if __name__ == "__main__":
    main()