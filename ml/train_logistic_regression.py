from pathlib import Path

import joblib
import numpy as np

from scipy.sparse import csr_matrix
from scipy.sparse import hstack

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.metrics import average_precision_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

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


print("Loading training data...")
train_data = load_training_data()

print("Loading validation data...")
validation_data = load_validation_data()


# Separate predictors and target.
X_train_numeric = train_data[NUMERIC_COLUMNS]
X_train_categorical = train_data[CATEGORICAL_COLUMNS]
y_train = train_data["is_fraud"]

X_validation_numeric = validation_data[NUMERIC_COLUMNS]
X_validation_categorical = validation_data[CATEGORICAL_COLUMNS]
y_validation = validation_data["is_fraud"]


# Scale numeric features.
scaler = StandardScaler()

X_train_numeric_scaled = scaler.fit_transform(
    X_train_numeric
)

X_validation_numeric_scaled = scaler.transform(
    X_validation_numeric
)


# Convert transaction types into numeric columns.
encoder = OneHotEncoder(
    handle_unknown="ignore",
    sparse_output=True,
)

X_train_categorical_encoded = encoder.fit_transform(
    X_train_categorical
)

X_validation_categorical_encoded = encoder.transform(
    X_validation_categorical
)


# Combine numeric and categorical features.
X_train = hstack(
    [
        csr_matrix(X_train_numeric_scaled),
        X_train_categorical_encoded,
    ],
    format="csr",
)

X_validation = hstack(
    [
        csr_matrix(X_validation_numeric_scaled),
        X_validation_categorical_encoded,
    ],
    format="csr",
)


# Train the model.
model = LogisticRegression(
    class_weight="balanced",
    max_iter=1000,
    random_state=42,
)

print("Training logistic regression...")
model.fit(X_train, y_train)


# Predict validation fraud probabilities.
validation_probabilities = model.predict_proba(
    X_validation
)[:, 1]

validation_predictions = (
    validation_probabilities >= 0.50
).astype(int)


# Calculate validation metrics.
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


print("\nLogistic Regression Validation Results")
print("--------------------------------------")
print(f"Accuracy:  {accuracy:.4%}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 score:  {f1:.4f}")
print(f"ROC-AUC:   {roc_auc:.4f}")
print(f"PR-AUC:    {pr_auc:.6f}")

print("\nConfusion matrix:")
print(matrix)


# Save the model and preprocessing objects together.
Path("models").mkdir(exist_ok=True)

model_bundle = {
    "model": model,
    "scaler": scaler,
    "encoder": encoder,
    "numeric_columns": NUMERIC_COLUMNS,
    "categorical_columns": CATEGORICAL_COLUMNS,
    "threshold": 0.50,
}

joblib.dump(
    model_bundle,
    "models/logistic_regression_v1.joblib",
)

print(
    "\nSaved model to "
    "models/logistic_regression_v1.joblib"
)