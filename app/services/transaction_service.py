from decimal import Decimal

from database.connection import get_connection


def transfer_money(sender_account_id, receiver_account_id, amount):
    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValueError("Transfer amount must be greater than zero")

    if sender_account_id == receiver_account_id:
        raise ValueError("Sender and receiver must be different")
    #assure atomic
    with get_connection() as connection:
        with connection.cursor() as cursor:
            # Lock both accounts until the transaction finishes.
            cursor.execute(
                """
                SELECT
                    account_id,
                    balance,
                    account_status
                FROM accounts
                WHERE account_id IN (%s, %s)
                ORDER BY account_id
                FOR UPDATE;
                """,
                (
                    sender_account_id,
                    receiver_account_id,
                ),
            )

            accounts = {
                row[0]: row
                for row in cursor.fetchall()
            }

            if sender_account_id not in accounts:
                raise ValueError("Sender account does not exist")

            if receiver_account_id not in accounts:
                raise ValueError("Receiver account does not exist")

            sender = accounts[sender_account_id]
            receiver = accounts[receiver_account_id]

            sender_balance = sender[1]
            receiver_balance = receiver[1]

            if sender[2] != "active":
                raise ValueError("Sender account is not active")

            if receiver[2] != "active":
                raise ValueError("Receiver account is not active")

            if sender_balance < amount:
                raise ValueError("Insufficient funds")

            new_sender_balance = sender_balance - amount
            new_receiver_balance = receiver_balance + amount

            cursor.execute(
                """
                UPDATE accounts
                SET balance = %s
                WHERE account_id = %s;
                """,
                (
                    new_sender_balance,
                    sender_account_id,
                ),
            )

            cursor.execute(
                """
                UPDATE accounts
                SET balance = %s
                WHERE account_id = %s;
                """,
                (
                    new_receiver_balance,
                    receiver_account_id,
                ),
            )

            cursor.execute(
                """
                INSERT INTO transactions (
                    data_source,
                    transaction_type,
                    amount,
                    origin_code,
                    old_balance_origin,
                    new_balance_origin,
                    destination_code,
                    old_balance_destination,
                    new_balance_destination,
                    rule_flagged_fraud,
                    sender_account_id,
                    receiver_account_id,
                    transaction_status
                )
                VALUES (
                    'application',
                    'TRANSFER',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE,
                    %s,
                    %s,
                    'completed'
                )
                RETURNING transaction_id;
                """,
                (
                    amount,
                    f"A{sender_account_id}",
                    sender_balance,
                    new_sender_balance,
                    f"A{receiver_account_id}",
                    receiver_balance,
                    new_receiver_balance,
                    sender_account_id,
                    receiver_account_id,
                ),
            )

            transaction_id = cursor.fetchone()[0]

    return transaction_id