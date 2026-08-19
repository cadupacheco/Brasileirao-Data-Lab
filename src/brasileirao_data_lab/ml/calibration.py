from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)

from brasileirao_data_lab.ml.baseline import (
    FEATURE_COLUMNS,
    Metrics,
    load_features,
    multiclass_brier_score,
)
from brasileirao_data_lab.ml.model_comparison import (
    build_random_forest,
)


# =============================================================================
# Configuração
# =============================================================================

BASE_TRAIN_MAX_SEASON = 2024
CALIBRATION_SEASON = 2025
REFERENCE_SEASON = 2026

MIN_TEMPERATURE = 0.25
MAX_TEMPERATURE = 4.00
PROBABILITY_EPSILON = 1e-12


# =============================================================================
# Estruturas
# =============================================================================


@dataclass(frozen=True)
class CalibrationSplit:
    base_train: pd.DataFrame
    calibration: pd.DataFrame
    reference: pd.DataFrame


@dataclass(frozen=True)
class CalibrationReport:
    temperature: float
    raw_reference: Metrics
    calibrated_reference: Metrics
    final_raw_reference: Metrics
    final_calibrated_reference: Metrics


# =============================================================================
# Split temporal
# =============================================================================


def build_calibration_split(
    dataframe: pd.DataFrame,
) -> CalibrationSplit:
    """
    Cria o split temporal usado para aprender a temperatura.

    Modelo base: 2021-2024
    Calibração: 2025
    Referência: 2026
    """

    base_train = dataframe[
        dataframe[
            "season"
        ] <= BASE_TRAIN_MAX_SEASON
    ].copy()

    calibration = dataframe[
        dataframe[
            "season"
        ] == CALIBRATION_SEASON
    ].copy()

    reference = dataframe[
        dataframe[
            "season"
        ] == REFERENCE_SEASON
    ].copy()

    if base_train.empty:
        raise ValueError(
            "Conjunto base de treino vazio."
        )

    if calibration.empty:
        raise ValueError(
            "Conjunto de calibração vazio."
        )

    if reference.empty:
        raise ValueError(
            "Conjunto de referência vazio."
        )

    return CalibrationSplit(
        base_train=base_train,
        calibration=calibration,
        reference=reference,
    )


# =============================================================================
# Temperature scaling
# =============================================================================


def temperature_scale_probabilities(
    probabilities: np.ndarray,
    temperature: float,
) -> np.ndarray:
    """
    Aplica temperature scaling a probabilidades multiclasse.

    Convertendo probabilidades em log-probabilidades, dividindo por T e
    normalizando novamente com softmax.
    """

    if temperature <= 0:
        raise ValueError(
            "A temperatura deve ser maior que zero."
        )

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    if probabilities.ndim != 2:
        raise ValueError(
            "probabilities deve ter duas dimensões."
        )

    clipped = np.clip(
        probabilities,
        PROBABILITY_EPSILON,
        1.0,
    )

    logits = np.log(
        clipped
    )

    scaled_logits = (
        logits
        / temperature
    )

    scaled_logits = (
        scaled_logits
        - scaled_logits.max(
            axis=1,
            keepdims=True,
        )
    )

    exponentials = np.exp(
        scaled_logits
    )

    return (
        exponentials
        / exponentials.sum(
            axis=1,
            keepdims=True,
        )
    )


def fit_temperature(
    y_true: pd.Series,
    probabilities: np.ndarray,
    classes: np.ndarray,
) -> float:
    """
    Aprende uma única temperatura minimizando log loss.

    Nenhum dado de 2026 participa desta otimização.
    """

    def objective(
        temperature: float,
    ) -> float:
        calibrated = (
            temperature_scale_probabilities(
                probabilities=probabilities,
                temperature=temperature,
            )
        )

        return float(
            log_loss(
                y_true,
                calibrated,
                labels=classes,
            )
        )

    result = minimize_scalar(
        objective,
        bounds=(
            MIN_TEMPERATURE,
            MAX_TEMPERATURE,
        ),
        method="bounded",
    )

    if not result.success:
        raise RuntimeError(
            "Falha ao ajustar temperature scaling."
        )

    return float(
        result.x
    )


# =============================================================================
# Métricas
# =============================================================================


def evaluate_probabilities(
    y_true: pd.Series,
    probabilities: np.ndarray,
    classes: np.ndarray,
) -> Metrics:
    """Avalia probabilidades multiclasse."""

    predictions = classes[
        np.argmax(
            probabilities,
            axis=1,
        )
    ]

    return Metrics(
        accuracy=float(
            accuracy_score(
                y_true,
                predictions,
            )
        ),
        log_loss=float(
            log_loss(
                y_true,
                probabilities,
                labels=classes,
            )
        ),
        brier=multiclass_brier_score(
            y_true=y_true,
            probabilities=probabilities,
            classes=classes,
        ),
    )


# =============================================================================
# Treino e calibração
# =============================================================================


def fit_random_forest(
    dataframe: pd.DataFrame,
):
    """Treina o Random Forest vencedor do backtest."""

    model = build_random_forest()

    model.fit(
        dataframe[
            list(
                FEATURE_COLUMNS
            )
        ],
        dataframe[
            "target"
        ],
    )

    return model


def run_temperature_calibration(
    dataframe: pd.DataFrame,
) -> CalibrationReport:
    """
    Aprende T em 2025 e verifica o efeito em 2026.

    Também aplica a mesma temperatura a um RF final retreinado em 2021-2025.
    """

    split = build_calibration_split(
        dataframe
    )

    calibration_model = fit_random_forest(
        split.base_train
    )

    classes = np.asarray(
        calibration_model.classes_
    )

    calibration_probabilities = (
        calibration_model.predict_proba(
            split.calibration[
                list(
                    FEATURE_COLUMNS
                )
            ]
        )
    )

    temperature = fit_temperature(
        y_true=split.calibration[
            "target"
        ],
        probabilities=calibration_probabilities,
        classes=classes,
    )

    reference_raw = (
        calibration_model.predict_proba(
            split.reference[
                list(
                    FEATURE_COLUMNS
                )
            ]
        )
    )

    reference_calibrated = (
        temperature_scale_probabilities(
            probabilities=reference_raw,
            temperature=temperature,
        )
    )

    raw_reference_metrics = (
        evaluate_probabilities(
            y_true=split.reference[
                "target"
            ],
            probabilities=reference_raw,
            classes=classes,
        )
    )

    calibrated_reference_metrics = (
        evaluate_probabilities(
            y_true=split.reference[
                "target"
            ],
            probabilities=reference_calibrated,
            classes=classes,
        )
    )

    final_train = dataframe[
        dataframe[
            "season"
        ] <= CALIBRATION_SEASON
    ].copy()

    final_model = fit_random_forest(
        final_train
    )

    final_classes = np.asarray(
        final_model.classes_
    )

    if not np.array_equal(
        classes,
        final_classes,
    ):
        raise ValueError(
            "A ordem das classes mudou entre os modelos."
        )

    final_reference_raw = (
        final_model.predict_proba(
            split.reference[
                list(
                    FEATURE_COLUMNS
                )
            ]
        )
    )

    final_reference_calibrated = (
        temperature_scale_probabilities(
            probabilities=final_reference_raw,
            temperature=temperature,
        )
    )

    final_raw_metrics = (
        evaluate_probabilities(
            y_true=split.reference[
                "target"
            ],
            probabilities=final_reference_raw,
            classes=final_classes,
        )
    )

    final_calibrated_metrics = (
        evaluate_probabilities(
            y_true=split.reference[
                "target"
            ],
            probabilities=final_reference_calibrated,
            classes=final_classes,
        )
    )

    return CalibrationReport(
        temperature=temperature,
        raw_reference=raw_reference_metrics,
        calibrated_reference=calibrated_reference_metrics,
        final_raw_reference=final_raw_metrics,
        final_calibrated_reference=final_calibrated_metrics,
    )


# =============================================================================
# Relatório
# =============================================================================


def print_metrics(
    label: str,
    metrics: Metrics,
) -> None:
    """Imprime uma linha de métricas."""

    print(
        f"{label:<30} "
        f"accuracy={metrics.accuracy:.4f} | "
        f"log_loss={metrics.log_loss:.4f} | "
        f"brier={metrics.brier:.4f}"
    )


def print_calibration_report(
    report: CalibrationReport,
) -> None:
    """Mostra o efeito da calibração."""

    print()
    print(
        "=" * 88
    )
    print(
        "[TEMPERATURE]"
    )
    print(
        "=" * 88
    )

    print(
        f"T = {report.temperature:.6f}"
    )

    if report.temperature > 1.0:
        print(
            "[INFO] T > 1: probabilidades ficam menos extremas."
        )
    elif report.temperature < 1.0:
        print(
            "[INFO] T < 1: probabilidades ficam mais extremas."
        )
    else:
        print(
            "[INFO] T ≈ 1: pouca correção necessária."
        )

    print()
    print(
        "=" * 88
    )
    print(
        "[REFERENCE 2026] RF treinado até 2024"
    )
    print(
        "=" * 88
    )

    print_metrics(
        "Sem calibração",
        report.raw_reference,
    )

    print_metrics(
        "Temperature scaling",
        report.calibrated_reference,
    )

    print()
    print(
        "=" * 88
    )
    print(
        "[PRODUCTION CANDIDATE] RF treinado até 2025"
    )
    print(
        "=" * 88
    )

    print_metrics(
        "Sem calibração",
        report.final_raw_reference,
    )

    print_metrics(
        "Temperature scaling",
        report.final_calibrated_reference,
    )

    print()
    print(
        "[INFO] A temperatura foi aprendida apenas com 2025."
    )
    print(
        "[INFO] 2026 não participou do ajuste."
    )


def run_calibration_report() -> CalibrationReport:
    """Carrega as features e executa a calibração."""

    dataframe = load_features()

    report = run_temperature_calibration(
        dataframe
    )

    print_calibration_report(
        report
    )

    return report