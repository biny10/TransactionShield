from ml.data_loader import load_test_data
from ml.data_loader import load_training_data
from ml.data_loader import load_validation_data


def print_summary(name, data):
    fraud_count = data["is_fraud"].sum()
    fraud_rate = data["is_fraud"].mean()

    print(f"{name}:")
    print(f"  Rows: {len(data):,}")
    print(f"  Fraud: {fraud_count:,}")
    print(f"  Fraud rate: {fraud_rate:.4%}")
    print()


train_data = load_training_data()
validation_data = load_validation_data()
test_data = load_test_data()


print_summary("Training", train_data)
print_summary("Validation", validation_data)
print_summary("Test", test_data)