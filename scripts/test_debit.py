from decimal import Decimal

from app.services.transaction_service import debit_account
from database.connection import get_connection


ACCOUNT_ID = 2
DEBIT_AMOUNT = Decimal("25.00")


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

transaction_id = debit_account(
    account_id=ACCOUNT_ID,
    amount=DEBIT_AMOUNT,
    destination_code="UTILITY_COMPANY",
)

balance_after = get_balance(ACCOUNT_ID)


print(f"Transaction ID: {transaction_id}")
print(f"Balance before: ${balance_before}")
print(f"Debit amount:   ${DEBIT_AMOUNT}")
print(f"Balance after:  ${balance_after}")

assert balance_after == balance_before - DEBIT_AMOUNT

print("\nTest passed: debit completed correctly.")