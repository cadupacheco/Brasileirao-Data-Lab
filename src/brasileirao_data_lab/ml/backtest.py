from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from brasileirao_data_lab.ml.baseline import (
    FEATURE_COLUMNS,
    Metrics,
    load_features,
)
from brasileirao_data_lab.ml.model_comparison import (
    build_candidate_models,
    evaluate_classifier,
)


# =============================================================================
# Configuração
# =============================================================================

BACKTEST_VALIDATION_SEASONS = (
    2023,
    2024,
    2025,
)

REFERENCE_TEST_SEASON = 2026


# =============================================================================
# Estruturas
# =============================================================================


@dataclass(frozen=True)
class FoldResult:
    model_name: str
    validation_season: int
    train_rows: int
    validation_rows: int
    metrics: Metrics


@dataclass(frozen=True)
class AggregateResult:
    model_name: str
    folds: int
    mean_accuracy: float
    mean_log_loss: float
    mean_brier: float


# =============================================================================
# Folds temporais
# =============================================================================


def build_backtest_fold(
    dataframe: pd.DataFrame,
    validation_season: int,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Cria um fold expanding-window.

    Exemplo para validation_season=2024:
    treino = 2021, 2022, 2023
    validação = 2024
    """

    train = dataframe[
        dataframe[
            "season"
        ] < validation_season
    ].copy()

    validation = dataframe[
        dataframe[
            "season"
        ] == validation_season
    ].copy()

    if train.empty:
        raise ValueError(
            "Conjunto de treino vazio para "
            f"validação em {validation_season}."
        )

    if validation.empty:
        raise ValueError(
            "Conjunto de validação vazio para "
            f"{validation_season}."
        )

    return (
        train,
        validation,
    )


# =============================================================================
# Backtest
# =============================================================================


def run_single_fold(
    dataframe: pd.DataFrame,
    validation_season: int,
) -> list[FoldResult]:
    """Treina todos os candidatos em um fold temporal."""

    train, validation = (
        build_backtest_fold(
            dataframe=dataframe,
            validation_season=validation_season,
        )
    )

    results: list[
        FoldResult
    ] = []

    for (
        model_name,
        model,
    ) in build_candidate_models().items():

        model.fit(
            train[
                list(
                    FEATURE_COLUMNS
                )
            ],
            train[
                "target"
            ],
        )

        metrics = evaluate_classifier(
            model=model,
            dataframe=validation,
        )

        results.append(
            FoldResult(
                model_name=model_name,
                validation_season=validation_season,
                train_rows=len(
                    train
                ),
                validation_rows=len(
                    validation
                ),
                metrics=metrics,
            )
        )

    return results


def aggregate_fold_results(
    fold_results: list[FoldResult],
) -> list[AggregateResult]:
    """Calcula médias das métricas por modelo."""

    if not fold_results:
        raise ValueError(
            "Nenhum resultado de fold foi informado."
        )

    rows = [
        {
            "model_name": result.model_name,
            "accuracy": result.metrics.accuracy,
            "log_loss": result.metrics.log_loss,
            "brier": result.metrics.brier,
        }
        for result in fold_results
    ]

    dataframe = pd.DataFrame(
        rows
    )

    grouped = (
        dataframe
        .groupby(
            "model_name",
            as_index=False,
        )
        .agg(
            folds=(
                "model_name",
                "size",
            ),
            mean_accuracy=(
                "accuracy",
                "mean",
            ),
            mean_log_loss=(
                "log_loss",
                "mean",
            ),
            mean_brier=(
                "brier",
                "mean",
            ),
        )
    )

    return [
        AggregateResult(
            model_name=str(
                row.model_name
            ),
            folds=int(
                row.folds
            ),
            mean_accuracy=float(
                row.mean_accuracy
            ),
            mean_log_loss=float(
                row.mean_log_loss
            ),
            mean_brier=float(
                row.mean_brier
            ),
        )
        for row in grouped.itertuples(
            index=False
        )
    ]


def select_backtest_winner(
    aggregate_results: list[
        AggregateResult
    ],
) -> str:
    """
    Seleciona o modelo mais consistente no backtest.

    Critério:
    1. menor média de log loss
    2. menor média de Brier
    3. maior média de accuracy
    """

    if not aggregate_results:
        raise ValueError(
            "Nenhum resultado agregado foi informado."
        )

    winner = min(
        aggregate_results,
        key=lambda result: (
            result.mean_log_loss,
            result.mean_brier,
            -result.mean_accuracy,
        ),
    )

    return winner.model_name


def run_walk_forward_backtest(
    dataframe: pd.DataFrame,
) -> tuple[
    list[FoldResult],
    list[AggregateResult],
    str,
]:
    """
    Executa o backtest expandindo o treino ano após ano.

    2026 não participa da seleção.
    """

    historical = dataframe[
        dataframe[
            "season"
        ] < REFERENCE_TEST_SEASON
    ].copy()

    fold_results: list[
        FoldResult
    ] = []

    for validation_season in (
        BACKTEST_VALIDATION_SEASONS
    ):
        fold_results.extend(
            run_single_fold(
                dataframe=historical,
                validation_season=validation_season,
            )
        )

    aggregate_results = (
        aggregate_fold_results(
            fold_results
        )
    )

    winner = select_backtest_winner(
        aggregate_results
    )

    return (
        fold_results,
        aggregate_results,
        winner,
    )


# =============================================================================
# Referência 2026
# =============================================================================


def evaluate_reference_test(
    dataframe: pd.DataFrame,
) -> dict[
    str,
    Metrics,
]:
    """
    Treina em 2021-2025 e avalia 2026 apenas como referência.

    Esses números não participam da escolha do modelo.
    """

    train = dataframe[
        dataframe[
            "season"
        ] < REFERENCE_TEST_SEASON
    ].copy()

    test = dataframe[
        dataframe[
            "season"
        ] == REFERENCE_TEST_SEASON
    ].copy()

    if train.empty:
        raise ValueError(
            "Treino final vazio."
        )

    if test.empty:
        raise ValueError(
            "Teste de referência 2026 vazio."
        )

    results: dict[
        str,
        Metrics,
    ] = {}

    for (
        model_name,
        model,
    ) in build_candidate_models().items():

        model.fit(
            train[
                list(
                    FEATURE_COLUMNS
                )
            ],
            train[
                "target"
            ],
        )

        results[
            model_name
        ] = evaluate_classifier(
            model=model,
            dataframe=test,
        )

    return results


# =============================================================================
# Relatório
# =============================================================================


def print_fold_results(
    fold_results: list[
        FoldResult
    ],
) -> None:
    """Imprime os resultados de cada temporada de validação."""

    print()
    print(
        "=" * 88
    )
    print(
        "[BACKTEST] Expanding-window"
    )
    print(
        "=" * 88
    )

    current_season: int | None = None

    for result in sorted(
        fold_results,
        key=lambda item: (
            item.validation_season,
            item.model_name,
        ),
    ):
        if (
            current_season
            != result.validation_season
        ):
            current_season = (
                result.validation_season
            )

            print()
            print(
                f"Validação {current_season} "
                f"| treino={result.train_rows} "
                f"| validação={result.validation_rows}"
            )

        metrics = result.metrics

        print(
            f"  {result.model_name:<21} "
            f"accuracy={metrics.accuracy:.4f} | "
            f"log_loss={metrics.log_loss:.4f} | "
            f"brier={metrics.brier:.4f}"
        )


def print_aggregate_results(
    aggregate_results: list[
        AggregateResult
    ],
    winner: str,
) -> None:
    """Imprime a média das métricas entre os folds."""

    print()
    print(
        "=" * 88
    )
    print(
        "[AGGREGATE] Média das validações 2023-2025"
    )
    print(
        "=" * 88
    )

    for result in sorted(
        aggregate_results,
        key=lambda item: (
            item.mean_log_loss,
            item.mean_brier,
            -item.mean_accuracy,
        ),
    ):
        print(
            f"{result.model_name:<22} "
            f"folds={result.folds} | "
            f"accuracy={result.mean_accuracy:.4f} | "
            f"log_loss={result.mean_log_loss:.4f} | "
            f"brier={result.mean_brier:.4f}"
        )

    print()
    print(
        "[WINNER] Modelo mais consistente no backtest:"
    )
    print(
        f"         {winner}"
    )


def print_reference_results(
    results: dict[
        str,
        Metrics,
    ],
) -> None:
    """Imprime 2026 separadamente, sem usá-lo na escolha."""

    print()
    print(
        "=" * 88
    )
    print(
        "[REFERENCE 2026] Treino 2021-2025"
    )
    print(
        "=" * 88
    )

    for (
        model_name,
        metrics,
    ) in results.items():
        print(
            f"{model_name:<22} "
            f"accuracy={metrics.accuracy:.4f} | "
            f"log_loss={metrics.log_loss:.4f} | "
            f"brier={metrics.brier:.4f}"
        )

    print()
    print(
        "[INFO] 2026 continua fora do critério de seleção."
    )


def run_backtest_report() -> str:
    """Executa backtest, agregação e referência 2026."""

    dataframe = load_features()

    (
        fold_results,
        aggregate_results,
        winner,
    ) = run_walk_forward_backtest(
        dataframe
    )

    print_fold_results(
        fold_results
    )

    print_aggregate_results(
        aggregate_results,
        winner,
    )

    reference_results = (
        evaluate_reference_test(
            dataframe
        )
    )

    print_reference_results(
        reference_results
    )

    return winner