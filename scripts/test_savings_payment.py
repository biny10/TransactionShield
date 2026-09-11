from decimal import Decimal

from app.services.transaction_service import make_payment
from database.connection import get_connection
from database.operations import create_account
from database.operations import create_customer
from database.operations import create_merchant


STARTING_BALANCE = Decimal("300.00")
PAYMENT_AMOUNT = Decimal("50.00")


def get_account_balance(account_id):
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


def count_application_payments():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM transactions
                WHERE data_source = 'application'
                  AND transaction_type = 'PAYMENT';
                """
            )

            return cursor.fetchone()[0]


customer = create_customer(
    first_name="Savings",
    last_name="Test",
)

savings_account = create_account(
    customer_id=customer[0],
    account_type="savings",
    starting_balance=STARTING_BALANCE,
)

merchant = create_merchant("M_TEST_STORE")

account_id = savings_account[0]
merchant_id = merchant[0]

balance_before = get_account_balance(account_id)
payment_count_before = count_application_payments()


try:
    make_payment(
        account_id=account_id,
        merchant_id=merchant_id,
        amount=PAYMENT_AMOUNT,
    )

except ValueError as error:
    print(f"Payment rejected: {error}")


balance_after = get_account_balance(account_id)
payment_count_after = count_application_payments()


print(f"\nBalance before: ${balance_before}")
print(f"Balance after:  ${balance_after}")

print(f"\nPayments before: {payment_count_before}")
print(f"Payments after:  {payment_count_after}")


assert balance_before == balance_after
assert payment_count_before == payment_count_after

print("\nTest passed: savings account payment was blocked.")