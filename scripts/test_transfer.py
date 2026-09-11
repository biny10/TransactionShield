from app.services.transaction_service import transfer_money
from database.connection import get_connection
from database.operations import create_account
from database.operations import create_customer


# Create the sender
sender_customer = create_customer(
    first_name="Sender",
    last_name="Test",
)

sender_account = create_account(
    customer_id=sender_customer[0],
    account_type="checking",
    starting_balance=500.00,
)


# Create the receiver
receiver_customer = create_customer(
    first_name="Receiver",
    last_name="Test",
)

receiver_account = create_account(
    customer_id=receiver_customer[0],
    account_type="checking",
    starting_balance=100.00,
)


# Transfer $125
transaction_id = transfer_money(
    sender_account_id=sender_account[0],
    receiver_account_id=receiver_account[0],
    amount=125.00,
)


# Retrieve the updated balances
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

        updated_accounts = cursor.fetchall()


print(f"Transaction ID: {transaction_id}")
print("Updated accounts:")

for account_id, balance in updated_accounts:
    print(f"Account {account_id}: ${balance}")