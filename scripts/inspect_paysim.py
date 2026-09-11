import pandas as pd


FILE_PATH = "data/raw/paysim.csv"
CHUNK_SIZE = 100_000

total_rows = 0
fraud_count = 0
flagged_fraud_count = 0

transaction_type_counts = {}

minimum_amount = float("inf")
maximum_amount = float("-inf")

balance_columns = [
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
]

negative_balance_counts = {
    column: 0 for column in balance_columns
}


for chunk in pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE):
    total_rows += len(chunk)

    fraud_count += chunk["isFraud"].sum()
    flagged_fraud_count += chunk["isFlaggedFraud"].sum()

    minimum_amount = min(minimum_amount, chunk["amount"].min())
    maximum_amount = max(maximum_amount, chunk["amount"].max())

    current_type_counts = chunk["type"].value_counts()

    for transaction_type, count in current_type_counts.items():
        transaction_type_counts[transaction_type] = (
            transaction_type_counts.get(transaction_type, 0) + count
        )

    for column in balance_columns:
        negative_balance_counts[column] += (chunk[column] < 0).sum()


print("PAYSim Dataset Summary")
print("----------------------")

print(f"Total rows: {total_rows:,}")
print(f"Fraudulent transactions: {fraud_count:,}")
print(f"Flagged transactions: {flagged_fraud_count:,}")

print(f"\nMinimum transaction amount: {minimum_amount:,.2f}")
print(f"Maximum transaction amount: {maximum_amount:,.2f}")

print("\nTransaction types:")

for transaction_type, count in sorted(transaction_type_counts.items()):
    print(f"  {transaction_type}: {count:,}")

print("\nNegative balance counts:")

for column, count in negative_balance_counts.items():
    print(f"  {column}: {count:,}")