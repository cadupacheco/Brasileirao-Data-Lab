from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    log_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# =============================================================================
# Configuração
# =============================================================================

TRAIN_MAX_SEASON = 2024
VALIDATION_SEASON = 2025
TEST_SEASON = 2026

CLASS_ORDER = (
    "AWAY",
    "DRAW",
    "HOME",
)

FEATURE_COLUMNS = (
    "ppg_diff",
    "goal_difference_per_game_diff",
    "recent_points_5_diff",
    "recent_points_10_diff",
    "venue_ppg_diff",
    "recent_goal_balance_5_diff",
    "elo_diff",
    "elo_expected_home_score",
    "h2h_meetings_before",
    "h2h_home_ppg_before",
    "h2h_away_ppg_before",
    "h2h_goal_difference_per_game_before",
    "h2h_recent_points_5_diff",
)


# =============================================================================
# Estruturas
# =============================================================================


@dataclass(frozen=True)
class Metrics:
    accuracy: float
    log_loss: float
    brier: float


@dataclass(frozen=True)
class DatasetSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_features_file() -> Path:
    """Retorna o dataset de features."""

    return (
        get_project_root()
        / "data"
        / "ml"
        / "features.csv"
    )


# =============================================================================
# Dataset
# =============================================================================


def load_features(
    path: Path | None = None,
) -> pd.DataFrame:
    """Carrega o dataset de features."""

    features_file = (
        path
        if path is not None
        else get_features_file()
    )

    if not features_file.exists():
        raise FileNotFoundError(
            "Dataset de features não encontrado em: "
            f"{features_file}"
        )

    dataframe = pd.read_csv(
        features_file
    )

    validate_features(
        dataframe
    )

    return dataframe


def validate_features(
    dataframe: pd.DataFrame,
) -> None:
    """Valida as colunas necessárias ao baseline."""

    required_columns = {
        "season",
        "target",
        *FEATURE_COLUMNS,
    }

    missing = (
        required_columns
        - set(
            dataframe.columns
        )
    )

    if missing:
        raise ValueError(
            "Colunas ausentes para o baseline: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    if dataframe.empty:
        raise ValueError(
            "Dataset de features vazio."
        )

    if dataframe[
        list(
            FEATURE_COLUMNS
        )
    ].isna().any().any():
        raise ValueError(
            "Existem valores nulos nas features do baseline."
        )


def split_by_time(
    dataframe: pd.DataFrame,
) -> DatasetSplit:
    """
    Divide o dataset cronologicamente.

    Não usamos split aleatório porque o objetivo é prever o futuro usando
    apenas temporadas anteriores.
    """

    train = dataframe[
        dataframe[
            "season"
        ] <= TRAIN_MAX_SEASON
    ].copy()

    validation = dataframe[
        dataframe[
            "season"
        ] == VALIDATION_SEASON
    ].copy()

    test = dataframe[
        dataframe[
            "season"
        ] == TEST_SEASON
    ].copy()

    if train.empty:
        raise ValueError(
            "Conjunto de treino vazio."
        )

    if validation.empty:
        raise ValueError(
            "Conjunto de validação vazio."
        )

    if test.empty:
        raise ValueError(
            "Conjunto de teste vazio."
        )

    return DatasetSplit(
        train=train,
        validation=validation,
        test=test,
    )


# =============================================================================
# Modelo
# =============================================================================


def build_model() -> Pipeline:
    """Cria o primeiro baseline probabilístico da V0.6."""

    return Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                LogisticRegression(
                    solver="lbfgs",
                    max_iter=2000,
                ),
            ),
        ]
    )


def train_model(
    train: pd.DataFrame,
) -> Pipeline:
    """Treina o baseline."""

    model = build_model()

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

    return model


# =============================================================================
# Métricas
# =============================================================================


def multiclass_brier_score(
    y_true: pd.Series,
    probabilities: np.ndarray,
    classes: np.ndarray,
) -> float:
    """Calcula o Brier Score multiclasse."""

    class_to_index = {
        label: index
        for index, label in enumerate(
            classes
        )
    }

    one_hot = np.zeros_like(
        probabilities,
        dtype=float,
    )

    for row_index, label in enumerate(
        y_true
    ):
        one_hot[
            row_index,
            class_to_index[
                label
            ],
        ] = 1.0

    squared_error = (
        probabilities
        - one_hot
    ) ** 2

    return float(
        np.mean(
            np.sum(
                squared_error,
                axis=1,
            )
        )
    )


def evaluate_model(
    model: Pipeline,
    dataframe: pd.DataFrame,
) -> Metrics:
    """Avalia accuracy e qualidade probabilística."""

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

    classes = model.named_steps[
        "model"
    ].classes_

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


def training_class_probabilities(
    train: pd.DataFrame,
) -> dict[str, float]:
    """Calcula o baseline ingênuo pela frequência das classes no treino."""

    distribution = (
        train[
            "target"
        ]
        .value_counts(
            normalize=True
        )
        .to_dict()
    )

    return {
        label: float(
            distribution.get(
                label,
                0.0,
            )
        )
        for label in CLASS_ORDER
    }


def evaluate_prior_baseline(
    train: pd.DataFrame,
    dataframe: pd.DataFrame,
) -> Metrics:
    """
    Avalia uma referência que ignora todas as features.

    Ela sempre prevê a mesma distribuição observada no conjunto de treino.
    """

    priors = training_class_probabilities(
        train
    )

    probabilities = np.tile(
        np.array(
            [
                priors[
                    label
                ]
                for label in CLASS_ORDER
            ],
            dtype=float,
        ),
        (
            len(
                dataframe
            ),
            1,
        ),
    )

    predicted_label = max(
        priors,
        key=priors.get,
    )

    predictions = np.full(
        len(
            dataframe
        ),
        predicted_label,
        dtype=object,
    )

    return Metrics(
        accuracy=float(
            accuracy_score(
                dataframe[
                    "target"
                ],
                predictions,
            )
        ),
        log_loss=float(
            log_loss(
                dataframe[
                    "target"
                ],
                probabilities,
                labels=list(
                    CLASS_ORDER
                ),
            )
        ),
        brier=multiclass_brier_score(
            y_true=dataframe[
                "target"
            ],
            probabilities=probabilities,
            classes=np.array(
                CLASS_ORDER
            ),
        ),
    )


def build_confusion_matrix(
    model: Pipeline,
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Retorna matriz de confusão com rótulos legíveis."""

    predictions = model.predict(
        dataframe[
            list(
                FEATURE_COLUMNS
            )
        ]
    )

    matrix = confusion_matrix(
        dataframe[
            "target"
        ],
        predictions,
        labels=list(
            CLASS_ORDER
        ),
    )

    return pd.DataFrame(
        matrix,
        index=[
            f"real_{label}"
            for label in CLASS_ORDER
        ],
        columns=[
            f"pred_{label}"
            for label in CLASS_ORDER
        ],
    )


# =============================================================================
# Relatório
# =============================================================================


def print_metrics(
    label: str,
    metrics: Metrics,
) -> None:
    """Imprime uma linha padronizada de métricas."""

    print(
        f"{label:<20} "
        f"accuracy={metrics.accuracy:.4f} | "
        f"log_loss={metrics.log_loss:.4f} | "
        f"brier={metrics.brier:.4f}"
    )


def run_baseline(
    dataframe: pd.DataFrame,
) -> Pipeline:
    """Treina e avalia o primeiro modelo da V0.6."""

    split = split_by_time(
        dataframe
    )

    print()
    print(
        "=" * 88
    )
    print(
        "[DATASET] Split temporal"
    )
    print(
        "=" * 88
    )

    print(
        f"Treino      <= {TRAIN_MAX_SEASON}: "
        f"{len(split.train)} jogos"
    )
    print(
        f"Validação    {VALIDATION_SEASON}: "
        f"{len(split.validation)} jogos"
    )
    print(
        f"Teste        {TEST_SEASON}: "
        f"{len(split.test)} jogos"
    )

    model = train_model(
        split.train
    )

    validation_metrics = evaluate_model(
        model,
        split.validation,
    )

    test_metrics = evaluate_model(
        model,
        split.test,
    )

    validation_prior = evaluate_prior_baseline(
        split.train,
        split.validation,
    )

    test_prior = evaluate_prior_baseline(
        split.train,
        split.test,
    )

    print()
    print(
        "=" * 88
    )
    print(
        "[METRICS] Regressão Logística"
    )
    print(
        "=" * 88
    )

    print_metrics(
        "Validação 2025",
        validation_metrics,
    )

    print_metrics(
        "Teste 2026",
        test_metrics,
    )

    print()
    print(
        "=" * 88
    )
    print(
        "[REFERENCE] Baseline ingênuo"
    )
    print(
        "=" * 88
    )

    print_metrics(
        "Validação 2025",
        validation_prior,
    )

    print_metrics(
        "Teste 2026",
        test_prior,
    )

    print()
    print(
        "=" * 88
    )
    print(
        "[CONFUSION MATRIX] Teste 2026"
    )
    print(
        "=" * 88
    )

    print(
        build_confusion_matrix(
            model,
            split.test,
        ).to_string()
    )

    return model