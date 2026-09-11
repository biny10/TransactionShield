import joblib
import numpy as np

from sklearn.metrics import accuracy_score
from sklearn.metrics import average_precision_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import roc_auc_score

from ml.data_loader import load_test_data


MODEL_PATH = "models/hist_gradient_boosting_v1.joblib"


print("Loading selected model...")
model_bundle = joblib.load(MODEL_PATH)

model = model_bundle["model"]
encoder = model_bundle["encoder"]
numeric_columns = model_bundle["numeric_columns"]
categorical_columns = model_bundle["categorical_columns"]
threshold = model_bundle["threshold"]


print("Loading untouched test data...")
test_data = load_test_data()

y_test = test_data["is_fraud"]


# Apply the preprocessing learned from training.
X_test_numeric = test_data[
    numeric_columns
].to_numpy(dtype=np.float32)

X_test_categorical = encoder.transform(
    test_data[categorical_columns]
)

X_test = np.column_stack(
    [
        X_test_numeric,
        X_test_categorical,
    ]
)


# Use the already-selected validation threshold.
test_probabilities = model.predict_proba(
    X_test
)[:, 1]

test_predictions = (
    test_probabilities >= threshold
).astype(int)


accuracy = accuracy_score(
    y_test,
    test_predictions,
)

precision = precision_score(
    y_test,
    test_predictions,
    zero_division=0,
)

recall = recall_score(
    y_test,
    test_predictions,
)

f1 = f1_score(
    y_test,
    test_predictions,
)

roc_auc = roc_auc_score(
    y_test,
    test_probabilities,
)

pr_auc = average_precision_score(
    y_test,
    test_probabilities,
)

matrix = confusion_matrix(
    y_test,
    test_predictions,
)

true_negative, false_positive, false_negative, true_positive = (
    matrix.ravel()
)


print("\nFinal Test Results")
print("------------------")
print(f"Threshold: {threshold:.6f}")
print(f"Accuracy:  {accuracy:.4%}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 score:  {f1:.4f}")
print(f"ROC-AUC:   {roc_auc:.4f}")
print(f"PR-AUC:    {pr_auc:.6f}")

print("\nConfusion matrix:")
print(matrix)

print(f"\nTrue negatives:  {true_negative:,}")
print(f"False positives: {false_positive:,}")
print(f"False negatives: {false_negative:,}")
print(f"True positives:  {true_positive:,}")

print(
    f"\nTotal alerts: "
    f"{false_positive + true_positive:,}"
)