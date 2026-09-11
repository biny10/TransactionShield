from app.services.transaction_service import transfer_money
from database.connection import get_connection


SENDER_ACCOUNT_ID = 2
RECEIVER_ACCOUNT_ID = 3


def get_test_state():
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
                    SENDER_ACCOUNT_ID,
                    RECEIVER_ACCOUNT_ID,
                ),
            )

            balances = cursor.fetchall()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM transactions
                WHERE data_source = 'application';
                """
            )

            transaction_count = cursor.fetchone()[0]

    return balances, transaction_count


balances_before, count_before = get_test_state()

try:
    transfer_money(
        sender_account_id=SENDER_ACCOUNT_ID,
        receiver_account_id=RECEIVER_ACCOUNT_ID,
        amount=1000.00,
    )

except ValueError as error:
    print(f"Transfer rejected: {error}")

balances_after, count_after = get_test_state()


print("\nBefore:", balances_before)
print("After: ", balances_after)

print(f"\nApplication transactions before: {count_before}")
print(f"Application transactions after:  {count_after}")


assert balances_before == balances_after
assert count_before == count_after

print("\nTest passed: no money moved and no transaction was created.")