from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)

from brasileirao_data_lab.ml.baseline import (
    FEATURE_COLUMNS,
    Metrics,
    build_model as build_logistic_regression,
    load_features,
    multiclass_brier_score,
    split_by_time,
)


# =============================================================================
# Configuração
# =============================================================================

RANDOM_STATE = 42


# =============================================================================
# Estruturas
# =============================================================================


@dataclass(frozen=True)
class ModelResult:
    name: str
    validation: Metrics
    test: Metrics


# =============================================================================
# Modelos
# =============================================================================


def build_random_forest() -> RandomForestClassifier:
    """
    Random Forest conservadora para o primeiro comparativo.

    A profundidade e o tamanho mínimo das folhas são limitados para reduzir
    overfitting no nosso dataset relativamente pequeno.
    """

    return RandomForestClassifier(
        n_estimators=500,
        max_depth=6,
        min_samples_leaf=10,
        max_features="sqrt",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )


def build_gradient_boosting() -> GradientBoostingClassifier:
    """
    Gradient Boosting para datasets pequenos/médios.

    Mantemos árvores rasas e learning rate baixo nesta primeira comparação.
    """

    return GradientBoostingClassifier(
        loss="log_loss",
        n_estimators=150,
        learning_rate=0.05,
        max_depth=2,
        min_samples_leaf=10,
        random_state=RANDOM_STATE,
    )


def build_candidate_models() -> dict[
    str,
    ClassifierMixin,
]:
    """Retorna os modelos candidatos da primeira comparação."""

    return {
        "logistic_regression": (
            build_logistic_regression()
        ),
        "random_forest": (
            build_random_forest()
        ),
        "gradient_boosting": (
            build_gradient_boosting()
        ),
    }


# =============================================================================
# Avaliação
# =============================================================================


def get_model_classes(
    model: ClassifierMixin,
) -> np.ndarray:
    """Retorna as classes de estimadores simples ou Pipelines."""

    if hasattr(
        model,
        "classes_",
    ):
        return np.asarray(
            model.classes_
        )

    named_steps = getattr(
        model,
        "named_steps",
        None,
    )

    if (
        named_steps is not None
        and "model" in named_steps
        and hasattr(
            named_steps["model"],
            "classes_",
        )
    ):
        return np.asarray(
            named_steps[
                "model"
            ].classes_
        )

    raise ValueError(
        "Não foi possível localizar as classes do modelo."
    )


def evaluate_classifier(
    model: ClassifierMixin,
    dataframe: pd.DataFrame,
) -> Metrics:
    """Avalia um classificador probabilístico."""

    x = dataframe[
        list(
            FEATURE_COLUMNS
        )
    ]

    y = dataframe[
        "target"
    ]

    predictions = model.predict(
        x
    )

    probabilities = model.predict_proba(
        x
    )

    classes = get_model_classes(
        model
    )

    return Metrics(
        accuracy=float(
            accuracy_score(
                y,
                predictions,
            )
        ),
        log_loss=float(
            log_loss(
                y,
                probabilities,
                labels=classes,
            )
        ),
        brier=multiclass_brier_score(
            y_true=y,
            probabilities=probabilities,
            classes=classes,
        ),
    )


def select_best_model_name(
    validation_metrics: dict[
        str,
        Metrics,
    ],
) -> str:
    """
    Seleciona o vencedor SOMENTE pela validação.

    Critério principal: menor log loss.
    Desempate: menor Brier.
    Segundo desempate: maior accuracy.
    """

    if not validation_metrics:
        raise ValueError(
            "Nenhum resultado de validação foi informado."
        )

    return min(
        validation_metrics,
        key=lambda name: (
            validation_metrics[
                name
            ].log_loss,
            validation_metrics[
                name
            ].brier,
            -validation_metrics[
                name
            ].accuracy,
        ),
    )


def compare_models(
    dataframe: pd.DataFrame,
) -> tuple[
    list[ModelResult],
    str,
]:
    """
    Treina os candidatos e compara validação/teste.

    O nome vencedor é escolhido exclusivamente pelos resultados de 2025.
    """

    split = split_by_time(
        dataframe
    )

    candidates = (
        build_candidate_models()
    )

    results: list[
        ModelResult
    ] = []

    validation_metrics: dict[
        str,
        Metrics,
    ] = {}

    for name, model in candidates.items():
        model.fit(
            split.train[
                list(
                    FEATURE_COLUMNS
                )
            ],
            split.train[
                "target"
            ],
        )

        validation = (
            evaluate_classifier(
                model,
                split.validation,
            )
        )

        test = evaluate_classifier(
            model,
            split.test,
        )

        validation_metrics[
            name
        ] = validation

        results.append(
            ModelResult(
                name=name,
                validation=validation,
                test=test,
            )
        )

    winner = select_best_model_name(
        validation_metrics
    )

    return (
        results,
        winner,
    )


# =============================================================================
# Relatório
# =============================================================================


def print_metric_line(
    label: str,
    metrics: Metrics,
) -> None:
    """Imprime métricas de forma padronizada."""

    print(
        f"{label:<22} "
        f"accuracy={metrics.accuracy:.4f} | "
        f"log_loss={metrics.log_loss:.4f} | "
        f"brier={metrics.brier:.4f}"
    )


def print_comparison(
    results: list[ModelResult],
    winner: str,
) -> None:
    """Mostra a comparação completa."""

    print()
    print(
        "=" * 88
    )
    print(
        "[VALIDATION 2025] Seleção de modelo"
    )
    print(
        "=" * 88
    )

    for result in results:
        print_metric_line(
            result.name,
            result.validation,
        )

    print()
    print(
        "[WINNER] Pelo menor log loss em 2025:"
    )
    print(
        f"         {winner}"
    )

    print()
    print(
        "=" * 88
    )
    print(
        "[TEST SNAPSHOT 2026] Conferência"
    )
    print(
        "=" * 88
    )

    for result in results:
        print_metric_line(
            result.name,
            result.test,
        )

    print()
    print(
        "[INFO] O vencedor NÃO é escolhido pelos números de 2026."
    )
    print(
        "[INFO] Mantemos a seleção baseada somente na validação de 2025."
    )


def run_model_comparison() -> tuple[
    list[ModelResult],
    str,
]:
    """Carrega as features e executa o comparativo."""

    dataframe = load_features()

    results, winner = compare_models(
        dataframe
    )

    print_comparison(
        results,
        winner,
    )

    return (
        results,
        winner,
    )