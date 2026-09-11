from decimal import Decimal

from app.services.transaction_service import make_payment
from database.connection import get_connection
from database.operations import create_merchant


ACCOUNT_ID = 2
PAYMENT_AMOUNT = Decimal("50.00")


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


merchant = create_merchant("M_TEST_STORE")
merchant_id = merchant[0]

balance_before = get_balance(ACCOUNT_ID)

transaction_id = make_payment(
    account_id=ACCOUNT_ID,
    merchant_id=merchant_id,
    amount=PAYMENT_AMOUNT,
)

balance_after = get_balance(ACCOUNT_ID)


print(f"Merchant: {merchant}")
print(f"Transaction ID: {transaction_id}")
print(f"Balance before: ${balance_before}")
print(f"Payment:        ${PAYMENT_AMOUNT}")
print(f"Balance after:  ${balance_after}")

assert balance_after == balance_before - PAYMENT_AMOUNT

print("\nTest passed: merchant payment completed correctly.")