from decimal import Decimal

from app.services.transaction_service import cash_in
from database.connection import get_connection


ACCOUNT_ID = 2
AMOUNT = Decimal("200.00")


def get_balance(account_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT balance
                FROM accounts
                WHERE account_id = %s;
                """,
                (account_id,),
            )

            return cursor.fetchone()[0]


balance_before = get_balance(ACCOUNT_ID)

transaction_id = cash_in(
    account_id=ACCOUNT_ID,
    amount=AMOUNT,
)

balance_after = get_balance(ACCOUNT_ID)


print(f"Transaction ID: {transaction_id}")
print(f"Balance before: ${balance_before}")
print(f"Cash added:     ${AMOUNT}")
print(f"Balance after:  ${balance_after}")

assert balance_after == balance_before + AMOUNT

print("Test passed: cash was added correctly.")