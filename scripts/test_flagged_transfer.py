from decimal import Decimal
from unittest.mock import patch

from app.services.transaction_service import transfer_money
from database.connection import get_connection
from database.operations import create_account
from database.operations import create_customer


# Create the sender.
sender_customer = create_customer(
    first_name="Flagged",
    last_name="Sender",
)

sender_account = create_account(
    customer_id=sender_customer[0],
    account_type="checking",
    starting_balance=500.00,
)


# Create the receiver.
receiver_customer = create_customer(
    first_name="Flagged",
    last_name="Receiver",
)

receiver_account = create_account(
    customer_id=receiver_customer[0],
    account_type="checking",
    starting_balance=100.00,
)


# Force the fraud model to return a fraudulent prediction.
forced_fraud_prediction = {
    "fraud_probability": 0.99999,
    "predicted_fraud": True,
    "threshold": 0.985122,
    "model_version": "hist_gradient_boosting_v1",
}


with patch(
    "app.services.transaction_service.predict_fraud",
    return_value=forced_fraud_prediction,
):
    transaction_id = transfer_money(
        sender_account_id=sender_account[0],
        receiver_account_id=receiver_account[0],
        amount=125.00,
    )


# Retrieve the balances, transaction, and prediction.
with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT account_id, balance
            FROM accounts
            WHERE account_id IN (%s, %s)
            ORDER BY account_id;
            """,
            (
                sender_account[0],
                receiver_account[0],
            ),
        )

        balances = dict(cursor.fetchall())

        cursor.execute(
            """
            SELECT
                t.transaction_status,
                fp.fraud_probability,
                fp.predicted_fraud,
                fp.model_version
            FROM transactions AS t
            JOIN fraud_predictions AS fp
                ON fp.transaction_id =
                    t.transaction_id
            WHERE t.transaction_id = %s;
            """,
            (transaction_id,),
        )

        transaction_result = cursor.fetchone()


transaction_status = transaction_result[0]
fraud_probability = transaction_result[1]
predicted_fraud = transaction_result[2]
model_version = transaction_result[3]


# Verify that the suspicious transfer was blocked.
assert transaction_status == "flagged"
assert predicted_fraud is True

assert balances[sender_account[0]] == Decimal("500.00")
assert balances[receiver_account[0]] == Decimal("100.00")


print("Flagged transfer test passed")
print(f"Transaction ID: {transaction_id}")
print(f"Status: {transaction_status}")
print(f"Fraud probability: {fraud_probability}")
print(f"Predicted fraud: {predicted_fraud}")
print(f"Model version: {model_version}")

print(
    "Sender balance:",
    balances[sender_account[0]],
)

print(
    "Receiver balance:",
    balances[receiver_account[0]],
)