from pathlib import Path

import joblib
import numpy as np

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import average_precision_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OrdinalEncoder

from ml.data_loader import load_training_data
from ml.data_loader import load_validation_data


NUMERIC_COLUMNS = [
    "amount",
    "old_balance_origin",
    "new_balance_origin",
    "old_balance_destination",
    "new_balance_destination",
]

CATEGORICAL_COLUMNS = [
    "transaction_type",
]

MINIMUM_RECALL = 0.90


print("Loading training data...")
train_data = load_training_data()

print("Loading validation data...")
validation_data = load_validation_data()


# HistGradientBoosting does not require numeric scaling.
X_train_numeric = train_data[
    NUMERIC_COLUMNS
].to_numpy(dtype=np.float32)

X_validation_numeric = validation_data[
    NUMERIC_COLUMNS
].to_numpy(dtype=np.float32)


# Convert transaction types into integer category codes.
encoder = OrdinalEncoder(
    handle_unknown="use_encoded_value",
    unknown_value=-1,
)

X_train_category = encoder.fit_transform(
    train_data[CATEGORICAL_COLUMNS]
)

X_validation_category = encoder.transform(
    validation_data[CATEGORICAL_COLUMNS]
)


# Combine numeric and categorical features.
X_train = np.column_stack(
    [
        X_train_numeric,
        X_train_category,
    ]
)

X_validation = np.column_stack(
    [
        X_validation_numeric,
        X_validation_category,
    ]
)

y_train = train_data["is_fraud"]
y_validation = validation_data["is_fraud"]


# The last column contains the categorical feature.
categorical_features = [
    False,
    False,
    False,
    False,
    False,
    True,
]


model = HistGradientBoostingClassifier(
    learning_rate=0.1,
    max_iter=200,
    max_leaf_nodes=31,
    min_samples_leaf=20,
    l2_regularization=1.0,
    class_weight="balanced",
    categorical_features=categorical_features,
    early_stopping=True,
    random_state=42,
)


print("Training HistGradientBoosting...")
model.fit(X_train, y_train)


validation_probabilities = model.predict_proba(
    X_validation
)[:, 1]


# Select a threshold with at least 90% recall.
precisions, recalls, thresholds = precision_recall_curve(
    y_validation,
    validation_probabilities,
)

precisions = precisions[:-1]
recalls = recalls[:-1]

valid_positions = np.where(
    recalls >= MINIMUM_RECALL
)[0]

if len(valid_positions) == 0:
    raise ValueError(
        "No threshold achieved the minimum recall"
    )

selected_position = valid_positions[
    np.argmax(precisions[valid_positions])
]

selected_threshold = thresholds[selected_position]

validation_predictions = (
    validation_probabilities >= selected_threshold
).astype(int)


accuracy = accuracy_score(
    y_validation,
    validation_predictions,
)

precision = precision_score(
    y_validation,
    validation_predictions,
    zero_division=0,
)

recall = recall_score(
    y_validation,
    validation_predictions,
)

f1 = f1_score(
    y_validation,
    validation_predictions,
)

roc_auc = roc_auc_score(
    y_validation,
    validation_probabilities,
)

pr_auc = average_precision_score(
    y_validation,
    validation_probabilities,
)

matrix = confusion_matrix(
    y_validation,
    validation_predictions,
)


print("\nHistGradientBoosting Validation Results")
print("---------------------------------------")
print(f"Threshold: {selected_threshold:.6f}")
print(f"Accuracy:  {accuracy:.4%}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 score:  {f1:.4f}")
print(f"ROC-AUC:   {roc_auc:.4f}")
print(f"PR-AUC:    {pr_auc:.6f}")

print("\nConfusion matrix:")
print(matrix)


Path("models").mkdir(exist_ok=True)

model_bundle = {
    "model": model,
    "encoder": encoder,
    "numeric_columns": NUMERIC_COLUMNS,
    "categorical_columns": CATEGORICAL_COLUMNS,
    "categorical_features": categorical_features,
    "threshold": float(selected_threshold),
}

joblib.dump(
    model_bundle,
    "models/hist_gradient_boosting_v1.joblib",
)

print(
    "\nSaved model to "
    "models/hist_gradient_boosting_v1.joblib"
)