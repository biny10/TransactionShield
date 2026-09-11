import joblib
import numpy as np

from scipy.sparse import csr_matrix
from scipy.sparse import hstack

from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score

from ml.data_loader import load_validation_data


MODEL_PATH = "models/logistic_regression_v1.joblib"
MINIMUM_RECALL = 0.90


print("Loading model...")
model_bundle = joblib.load(MODEL_PATH)

model = model_bundle["model"]
scaler = model_bundle["scaler"]
encoder = model_bundle["encoder"]

numeric_columns = model_bundle["numeric_columns"]
categorical_columns = model_bundle["categorical_columns"]


print("Loading validation data...")
validation_data = load_validation_data()

y_validation = validation_data["is_fraud"]


# Apply the preprocessing learned from training data.
numeric_scaled = scaler.transform(
    validation_data[numeric_columns]
)

categorical_encoded = encoder.transform(
    validation_data[categorical_columns]
)

X_validation = hstack(
    [
        csr_matrix(numeric_scaled),
        categorical_encoded,
    ],
    format="csr",
)


# Get probabilities instead of fixed predictions.
probabilities = model.predict_proba(
    X_validation
)[:, 1]


# Evaluate every possible threshold.
precisions, recalls, thresholds = precision_recall_curve(
    y_validation,
    probabilities,
)

# The last precision and recall values do not have
# corresponding thresholds.
precisions = precisions[:-1]
recalls = recalls[:-1]


# Keep thresholds with at least 90% fraud recall.
valid_positions = np.where(
    recalls >= MINIMUM_RECALL
)[0]

if len(valid_positions) == 0:
    raise ValueError(
        "No threshold achieved the minimum recall"
    )


# From the valid choices, select the highest precision.
best_position = valid_positions[
    np.argmax(precisions[valid_positions])
]

selected_threshold = thresholds[best_position]


predictions = (
    probabilities >= selected_threshold
).astype(int)


accuracy = accuracy_score(
    y_validation,
    predictions,
)

precision = precision_score(
    y_validation,
    predictions,
    zero_division=0,
)

recall = recall_score(
    y_validation,
    predictions,
)

f1 = f1_score(
    y_validation,
    predictions,
)

matrix = confusion_matrix(
    y_validation,
    predictions,
)

true_negative, false_positive, false_negative, true_positive = (
    matrix.ravel()
)


print("\nSelected Threshold Results")
print("--------------------------")
print(f"Threshold: {selected_threshold:.6f}")
print(f"Accuracy:  {accuracy:.4%}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 score:  {f1:.4f}")

print("\nConfusion matrix:")
print(matrix)

print(f"\nTrue negatives:  {true_negative:,}")
print(f"False positives: {false_positive:,}")
print(f"False negatives: {false_negative:,}")
print(f"True positives:  {true_positive:,}")


# Store the selected threshold with the model.
model_bundle["threshold"] = float(
    selected_threshold
)

joblib.dump(
    model_bundle,
    MODEL_PATH,
)

print(f"\nUpdated threshold saved to {MODEL_PATH}")