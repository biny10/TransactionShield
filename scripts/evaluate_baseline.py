import numpy as np

from sklearn.metrics import accuracy_score
from sklearn.metrics import average_precision_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import roc_auc_score

from ml.data_loader import load_validation_data


validation_data = load_validation_data()

y_validation = validation_data["is_fraud"]

# Baseline predicts every transaction as non-fraud.
baseline_predictions = np.zeros(
    len(y_validation),
    dtype=int,
)

baseline_probabilities = np.zeros(
    len(y_validation),
    dtype=float,
)


accuracy = accuracy_score(
    y_validation,
    baseline_predictions,
)

precision = precision_score(
    y_validation,
    baseline_predictions,
    zero_division=0,
)

recall = recall_score(
    y_validation,
    baseline_predictions,
)

f1 = f1_score(
    y_validation,
    baseline_predictions,
)

roc_auc = roc_auc_score(
    y_validation,
    baseline_probabilities,
)

pr_auc = average_precision_score(
    y_validation,
    baseline_probabilities,
)

matrix = confusion_matrix(
    y_validation,
    baseline_predictions,
)


print("Non-fraud Baseline")
print("------------------")
print(f"Accuracy:  {accuracy:.4%}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 score:  {f1:.4f}")
print(f"ROC-AUC:   {roc_auc:.4f}")
print(f"PR-AUC:    {pr_auc:.6f}")

print("\nConfusion matrix:")
print(matrix)