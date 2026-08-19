from __future__ import annotations

from brasileirao_data_lab.ml.features import (
    build_feature_dataset,
    load_history_dataframe,
    print_feature_summary,
    save_feature_dataset,
)


def main() -> None:
    print(
        "⚽ Brasileirão Data Lab - Feature Engineering V0.6"
    )
    print(
        "[INFO] Construindo features somente com informações "
        "disponíveis antes de cada partida."
    )

    history = load_history_dataframe()

    features = build_feature_dataset(
        history
    )

    print_feature_summary(
        features
    )

    output_file = save_feature_dataset(
        features
    )

    print()
    print(
        "[SUCCESS] Dataset de features salvo em:"
    )
    print(
        output_file
    )


if __name__ == "__main__":
    main()