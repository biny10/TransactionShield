from app.services.fraud_service import predict_fraud
from database.connection import get_connection


def get_example(actual_fraud):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    transaction_type,
                    amount,
                    old_balance_origin,
                    new_balance_origin,
                    old_balance_destination,
                    new_balance_destination,
                    actual_fraud
                FROM transactions
                WHERE data_source = 'paysim'
                  AND actual_fraud = %s
                  AND MOD(transaction_id, 10) = 0
                LIMIT 1;
                """,
                (actual_fraud,),
            )

            return cursor.fetchone()


def score_example(example):
    result = predict_fraud(
        transaction_type=example[0],
        amount=example[1],
        old_balance_origin=example[2],
        new_balance_origin=example[3],
        old_balance_destination=example[4],
        new_balance_destination=example[5],
    )

    print(f"Actual fraud:    {example[6]}")
    print(
        "Predicted fraud: "
        f"{result['predicted_fraud']}"
    )
    print(
        "Probability:     "
        f"{result['fraud_probability']:.6f}"
    )
    print(
        "Threshold:       "
        f"{result['threshold']:.6f}"
    )
    print()


fraud_example = get_example(True)
normal_example = get_example(False)

print("Fraud example")
print("-------------")
score_example(fraud_example)

print("Normal example")
print("--------------")
score_example(normal_example)