from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from brasileirao_data_lab.ml.baseline import (
    FEATURE_COLUMNS,
)
from brasileirao_data_lab.ml.features import (
    TeamState,
    build_difference_features,
    build_team_features,
    load_history_dataframe,
    update_team_state,
)
from brasileirao_data_lab.ml.model_comparison import (
    build_random_forest,
)
from brasileirao_data_lab.ml.ratings import (
    H2HState,
    build_h2h_features,
    expected_home_score,
    get_elo_rating,
    regress_elo_ratings_for_new_season,
    update_elo_ratings,
    update_h2h_state,
)
from brasileirao_data_lab.ml.team_identity import (
    canonical_team_key,
)


# =============================================================================
# Configuração
# =============================================================================

CURRENT_SEASON = 2026

PREDICTION_CLASS_ORDER = (
    "AWAY",
    "DRAW",
    "HOME",
)


# =============================================================================
# Estruturas
# =============================================================================


@dataclass
class PredictionContext:
    """Estado atual necessário para prever partidas futuras."""

    current_season: int
    season_states: dict[
        str,
        TeamState,
    ]
    elo_ratings: dict[
        str,
        float,
    ]
    h2h_states: dict[
        tuple[str, str],
        H2HState,
    ]


# =============================================================================
# Caminhos
# =============================================================================


def get_project_root() -> Path:
    """Retorna a raiz do projeto."""

    return Path(__file__).resolve().parents[3]


def get_predictions_file() -> Path:
    """Retorna o CSV com previsões de jogos futuros."""

    return (
        get_project_root()
        / "data"
        / "ml"
        / "future_predictions.csv"
    )


# =============================================================================
# Preparação dos jogos disputados
# =============================================================================


def prepare_played_history(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """Mantém somente jogos disputados e ordena cronologicamente."""

    played = history[
        history[
            "status"
        ] == "played"
    ].copy()

    if played.empty:
        raise ValueError(
            "Nenhuma partida disputada encontrada."
        )

    played[
        "match_datetime"
    ] = pd.to_datetime(
        played[
            "date"
        ].astype(str)
        + " "
        + played[
            "time"
        ].astype(str),
        errors="raise",
    )

    return played.sort_values(
        by=[
            "season",
            "match_datetime",
            "match_id",
        ]
    ).reset_index(
        drop=True
    )


# =============================================================================
# Reconstrução do estado atual
# =============================================================================


def build_prediction_context(
    history: pd.DataFrame,
) -> PredictionContext:
    """
    Reconstrói o estado atual usando apenas jogos já disputados.

    Estatísticas de temporada zeram a cada ano.
    Elo e H2H atravessam temporadas.
    """

    played = prepare_played_history(
        history
    )

    current_season: int | None = None

    season_states: dict[
        str,
        TeamState,
    ] = {}

    elo_ratings: dict[
        str,
        float,
    ] = {}

    h2h_states: dict[
        tuple[str, str],
        H2HState,
    ] = {}

    for row in played.itertuples(
        index=False
    ):
        season = int(
            row.season
        )

        if current_season != season:
            if current_season is not None:
                regress_elo_ratings_for_new_season(
                    elo_ratings
                )

            current_season = season
            season_states = {}

        home_team_key = canonical_team_key(
            str(
                row.home_team
            )
        )

        away_team_key = canonical_team_key(
            str(
                row.away_team
            )
        )

        home_state = season_states.setdefault(
            home_team_key,
            TeamState(),
        )

        away_state = season_states.setdefault(
            away_team_key,
            TeamState(),
        )

        home_goals = int(
            row.home_goals
        )

        away_goals = int(
            row.away_goals
        )

        update_team_state(
            state=home_state,
            goals_for=home_goals,
            goals_against=away_goals,
            venue="home",
        )

        update_team_state(
            state=away_state,
            goals_for=away_goals,
            goals_against=home_goals,
            venue="away",
        )

        update_elo_ratings(
            ratings=elo_ratings,
            home_team_key=home_team_key,
            away_team_key=away_team_key,
            home_goals=home_goals,
            away_goals=away_goals,
        )

        update_h2h_state(
            states=h2h_states,
            home_team_key=home_team_key,
            away_team_key=away_team_key,
            home_goals=home_goals,
            away_goals=away_goals,
        )

    if current_season is None:
        raise ValueError(
            "Não foi possível identificar a temporada atual."
        )

    return PredictionContext(
        current_season=current_season,
        season_states=season_states,
        elo_ratings=elo_ratings,
        h2h_states=h2h_states,
    )


# =============================================================================
# Features das partidas futuras
# =============================================================================


def build_future_match_features(
    match: pd.Series,
    context: PredictionContext,
) -> dict[str, object]:
    """Cria as features de uma partida futura no estado atual."""

    home_team_key = canonical_team_key(
        str(
            match[
                "home_team"
            ]
        )
    )

    away_team_key = canonical_team_key(
        str(
            match[
                "away_team"
            ]
        )
    )

    home_state = context.season_states.get(
        home_team_key,
        TeamState(),
    )

    away_state = context.season_states.get(
        away_team_key,
        TeamState(),
    )

    home_features = build_team_features(
        state=home_state,
        prefix="home",
        venue="home",
    )

    away_features = build_team_features(
        state=away_state,
        prefix="away",
        venue="away",
    )

    difference_features = build_difference_features(
        home_features,
        away_features,
    )

    home_elo = get_elo_rating(
        context.elo_ratings,
        home_team_key,
    )

    away_elo = get_elo_rating(
        context.elo_ratings,
        away_team_key,
    )

    elo_features = {
        "home_elo_before": float(
            home_elo
        ),
        "away_elo_before": float(
            away_elo
        ),
        "elo_diff": float(
            home_elo
            - away_elo
        ),
        "elo_expected_home_score": (
            expected_home_score(
                home_elo,
                away_elo,
            )
        ),
    }

    h2h_features = build_h2h_features(
        states=context.h2h_states,
        home_team_key=home_team_key,
        away_team_key=away_team_key,
    )

    return {
        "season": int(
            match[
                "season"
            ]
        ),
        "round": int(
            match[
                "round"
            ]
        ),
        "match_id": int(
            match[
                "match_id"
            ]
        ),
        "date": (
            None
            if pd.isna(
                match[
                    "date"
                ]
            )
            else str(
                match[
                    "date"
                ]
            )
        ),
        "time": (
            None
            if pd.isna(
                match[
                    "time"
                ]
            )
            else str(
                match[
                    "time"
                ]
            )
        ),
        "home_team_id": int(
            match[
                "home_team_id"
            ]
        ),
        "home_team": str(
            match[
                "home_team"
            ]
        ),
        "home_team_key": home_team_key,
        "away_team_id": int(
            match[
                "away_team_id"
            ]
        ),
        "away_team": str(
            match[
                "away_team"
            ]
        ),
        "away_team_key": away_team_key,
        **home_features,
        **away_features,
        **difference_features,
        **elo_features,
        **h2h_features,
    }


def build_future_feature_dataframe(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria features para todas as partidas ainda não disputadas da temporada atual.

    Cada jogo usa o mesmo snapshot atual. Não simulamos resultados futuros aqui.
    """

    context = build_prediction_context(
        history
    )

    future_matches = history[
        (
            history[
                "season"
            ] == context.current_season
        )
        & (
            history[
                "status"
            ] == "upcoming"
        )
    ].copy()

    if future_matches.empty:
        raise ValueError(
            "Nenhuma partida futura encontrada."
        )

    future_matches = future_matches.sort_values(
        by=[
            "round",
            "match_number",
            "match_id",
        ],
        na_position="last",
    ).reset_index(
        drop=True
    )

    rows = [
        build_future_match_features(
            match=row,
            context=context,
        )
        for _, row in future_matches.iterrows()
    ]

    dataframe = pd.DataFrame(
        rows
    )

    missing_features = (
        set(
            FEATURE_COLUMNS
        )
        - set(
            dataframe.columns
        )
    )

    if missing_features:
        raise ValueError(
            "Features ausentes para previsão: "
            + ", ".join(
                sorted(
                    missing_features
                )
            )
        )

    if dataframe[
        list(
            FEATURE_COLUMNS
        )
    ].isna().any().any():
        raise ValueError(
            "Existem valores nulos nas features futuras."
        )

    return dataframe


# =============================================================================
# Modelo final
# =============================================================================


def train_final_model(
    feature_dataset: pd.DataFrame,
):
    """
    Treina o Random Forest final com todas as partidas disputadas disponíveis.
    """

    if feature_dataset.empty:
        raise ValueError(
            "Dataset de treino vazio."
        )

    model = build_random_forest()

    model.fit(
        feature_dataset[
            list(
                FEATURE_COLUMNS
            )
        ],
        feature_dataset[
            "target"
        ],
    )

    return model


# =============================================================================
# Previsões
# =============================================================================


def probability_for_class(
    probabilities: np.ndarray,
    classes: np.ndarray,
    class_name: str,
) -> np.ndarray:
    """Retorna a coluna de probabilidade correspondente a uma classe."""

    positions = np.where(
        classes == class_name
    )[0]

    if len(
        positions
    ) != 1:
        raise ValueError(
            f"Classe inesperada no modelo: {class_name}."
        )

    return probabilities[
        :,
        int(
            positions[0]
        ),
    ]


def build_predictions_dataframe(
    model,
    future_features: pd.DataFrame,
) -> pd.DataFrame:
    """Aplica o modelo e monta o DataFrame final de previsões."""

    probabilities = model.predict_proba(
        future_features[
            list(
                FEATURE_COLUMNS
            )
        ]
    )

    classes = np.asarray(
        model.classes_
    )

    home_probability = probability_for_class(
        probabilities,
        classes,
        "HOME",
    )

    draw_probability = probability_for_class(
        probabilities,
        classes,
        "DRAW",
    )

    away_probability = probability_for_class(
        probabilities,
        classes,
        "AWAY",
    )

    predictions = future_features[
        [
            "season",
            "round",
            "match_id",
            "date",
            "time",
            "home_team_id",
            "home_team",
            "home_team_key",
            "away_team_id",
            "away_team",
            "away_team_key",
        ]
    ].copy()

    predictions[
        "home_probability"
    ] = home_probability

    predictions[
        "draw_probability"
    ] = draw_probability

    predictions[
        "away_probability"
    ] = away_probability

    predictions[
        "predicted_result"
    ] = classes[
        np.argmax(
            probabilities,
            axis=1,
        )
    ]

    predictions[
        "home_probability_pct"
    ] = (
        predictions[
            "home_probability"
        ]
        * 100.0
    ).round(
        1
    )

    predictions[
        "draw_probability_pct"
    ] = (
        predictions[
            "draw_probability"
        ]
        * 100.0
    ).round(
        1
    )

    predictions[
        "away_probability_pct"
    ] = (
        predictions[
            "away_probability"
        ]
        * 100.0
    ).round(
        1
    )

    validate_predictions(
        predictions
    )

    return predictions


def validate_predictions(
    predictions: pd.DataFrame,
) -> None:
    """Valida as previsões geradas."""

    if predictions.empty:
        raise ValueError(
            "Nenhuma previsão foi gerada."
        )

    probability_columns = [
        "home_probability",
        "draw_probability",
        "away_probability",
    ]

    if predictions[
        probability_columns
    ].isna().any().any():
        raise ValueError(
            "Existem probabilidades nulas."
        )

    sums = predictions[
        probability_columns
    ].sum(
        axis=1
    )

    if not np.allclose(
        sums.to_numpy(),
        1.0,
        atol=1e-8,
    ):
        raise ValueError(
            "As probabilidades não somam 1."
        )

    if (
        predictions[
            probability_columns
        ] < 0.0
    ).any().any():
        raise ValueError(
            "Foram encontradas probabilidades negativas."
        )

    if (
        predictions[
            probability_columns
        ] > 1.0
    ).any().any():
        raise ValueError(
            "Foram encontradas probabilidades acima de 1."
        )


# =============================================================================
# Persistência
# =============================================================================


def save_predictions(
    predictions: pd.DataFrame,
    output_file: Path | None = None,
) -> Path:
    """Salva as previsões em CSV."""

    path = (
        output_file
        if output_file is not None
        else get_predictions_file()
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
    )

    return path


# =============================================================================
# Execução completa
# =============================================================================


def generate_future_predictions(
    feature_dataset: pd.DataFrame,
    history: pd.DataFrame,
) -> pd.DataFrame:
    """Treina o modelo final e prevê todas as partidas futuras."""

    model = train_final_model(
        feature_dataset
    )

    future_features = (
        build_future_feature_dataframe(
            history
        )
    )

    return build_predictions_dataframe(
        model=model,
        future_features=future_features,
    )


# =============================================================================
# Resumo
# =============================================================================


def print_prediction_summary(
    predictions: pd.DataFrame,
    preview_rows: int = 10,
) -> None:
    """Mostra um resumo das previsões."""

    print()
    print(
        "=" * 88
    )
    print(
        "[SUMMARY] Previsões futuras"
    )
    print(
        "=" * 88
    )

    print(
        f"Partidas previstas: {len(predictions)}"
    )

    print()
    print(
        f"Primeiras {min(preview_rows, len(predictions))} partidas:"
    )

    for row in predictions.head(
        preview_rows
    ).itertuples(
        index=False
    ):
        print(
            f"  Rodada {int(row.round):02d} | "
            f"{row.home_team} "
            f"{row.home_probability_pct:.1f}% | "
            f"Empate {row.draw_probability_pct:.1f}% | "
            f"{row.away_team} "
            f"{row.away_probability_pct:.1f}%"
        )