from __future__ import annotations

from brasileirao_data_lab.ml.features import (
    load_history_dataframe,
)
from brasileirao_data_lab.ml.simulation import (
    DEFAULT_RANDOM_SEED,
    DEFAULT_SIMULATIONS,
    load_predictions,
    print_simulation_summary,
    save_simulation,
    simulate_season,
)


def main() -> None:
    print(
        "⚽ Brasileirão Data Lab - Monte Carlo V0.6"
    )
    print(
        f"[INFO] Simulações: {DEFAULT_SIMULATIONS:,}".replace(
            ",",
            ".",
        )
    )
    print(
        f"[INFO] Seed: {DEFAULT_RANDOM_SEED}"
    )
    print(
        "[INFO] Cada jogo usa as probabilidades do Random Forest."
    )
    print(
        "[INFO] Placares são amostrados do histórico, "
        "condicionados ao resultado."
    )

    history = load_history_dataframe()

    predictions = load_predictions()

    simulation = simulate_season(
        history=history,
        predictions=predictions,
        simulations=DEFAULT_SIMULATIONS,
        seed=DEFAULT_RANDOM_SEED,
    )

    print_simulation_summary(
        simulation
    )

    output_file = save_simulation(
        simulation
    )

    print()
    print(
        "[SUCCESS] Simulação salva em:"
    )
    print(
        output_file
    )


if __name__ == "__main__":
    main()