from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "hist_gradient_boosting_v1.joblib"
)

MODEL_VERSION = "hist_gradient_boosting_v1"


@lru_cache(maxsize=1)
def load_model_bundle():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Fraud model not found at "
            f"{MODEL_PATH}. Run "
            "'python -m "
            "ml.train_hist_gradient_boosting' "
            "to create it."
        )

    return joblib.load(MODEL_PATH)


def predict_fraud(
    transaction_type,
    amount,
    old_balance_origin,
    new_balance_origin,
    old_balance_destination,
    new_balance_destination,
):
    model_bundle = load_model_bundle()

    model = model_bundle["model"]
    encoder = model_bundle["encoder"]
    threshold = model_bundle["threshold"]

    numeric_values = np.array(
        [
            [
                amount,
                old_balance_origin,
                new_balance_origin,
                old_balance_destination,
                new_balance_destination,
            ]
        ],
        dtype=np.float32,
    )

    categorical_values = pd.DataFrame(
        {
            "transaction_type": [
                transaction_type
            ]
        }
    )

    encoded_category = encoder.transform(
        categorical_values
    )

    model_input = np.column_stack(
        [
            numeric_values,
            encoded_category,
        ]
    )

    fraud_probability = float(
        model.predict_proba(model_input)[0, 1]
    )

    predicted_fraud = (
        fraud_probability >= threshold
    )

    return {
        "fraud_probability": fraud_probability,
        "predicted_fraud": predicted_fraud,
        "threshold": threshold,
        "model_version": MODEL_VERSION,
    }


def store_fraud_prediction(
    cursor,
    transaction_id,
    prediction,
):
    cursor.execute(
        """
        INSERT INTO fraud_predictions (
            transaction_id,
            fraud_probability,
            predicted_fraud,
            model_version
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (
            transaction_id,
            model_version
        )
        DO UPDATE SET
            fraud_probability =
                EXCLUDED.fraud_probability,
            predicted_fraud =
                EXCLUDED.predicted_fraud,
            created_at = CURRENT_TIMESTAMP;
        """,
        (
            transaction_id,
            prediction["fraud_probability"],
            prediction["predicted_fraud"],
            prediction["model_version"],
        ),
    )