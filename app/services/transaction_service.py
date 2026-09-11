from decimal import Decimal

from database.connection import get_connection

from app.services.fraud_service import predict_fraud
from app.services.fraud_service import store_fraud_prediction
####Transfer###
def transfer_money(
    sender_account_id,
    receiver_account_id,
    amount,
):
    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValueError(
            "Transfer amount must be greater than zero"
        )

    if sender_account_id == receiver_account_id:
        raise ValueError(
            "Sender and receiver must be different"
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
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
                raise ValueError(
                    "Sender account does not exist"
                )

            if receiver_account_id not in accounts:
                raise ValueError(
                    "Receiver account does not exist"
                )

            sender = accounts[sender_account_id]
            receiver = accounts[receiver_account_id]

            sender_balance = sender[1]
            receiver_balance = receiver[1]

            if sender[2] != "active":
                raise ValueError(
                    "Sender account is not active"
                )

            if receiver[2] != "active":
                raise ValueError(
                    "Receiver account is not active"
                )

            if sender_balance < amount:
                raise ValueError("Insufficient funds")

            proposed_sender_balance = (
                sender_balance - amount
            )

            proposed_receiver_balance = (
                receiver_balance + amount
            )

            prediction = predict_fraud(
                transaction_type="TRANSFER",
                amount=amount,
                old_balance_origin=sender_balance,
                new_balance_origin=(
                    proposed_sender_balance
                ),
                old_balance_destination=(
                    receiver_balance
                ),
                new_balance_destination=(
                    proposed_receiver_balance
                ),
            )

            if prediction["predicted_fraud"]:
                transaction_status = "flagged"

            else:
                transaction_status = "completed"

                cursor.execute(
                    """
                    UPDATE accounts
                    SET balance = %s
                    WHERE account_id = %s;
                    """,
                    (
                        proposed_sender_balance,
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
                        proposed_receiver_balance,
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
                    origin_account_id,
                    destination_account_id,
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
                    %s
                )
                RETURNING transaction_id;
                """,
                (
                    amount,
                    f"A{sender_account_id}",
                    sender_balance,
                    proposed_sender_balance,
                    f"A{receiver_account_id}",
                    receiver_balance,
                    proposed_receiver_balance,
                    sender_account_id,
                    receiver_account_id,
                    transaction_status,
                ),
            )

            transaction_id = cursor.fetchone()[0]

            store_fraud_prediction(
                cursor=cursor,
                transaction_id=transaction_id,
                prediction=prediction,
            )

    return transaction_id
####CASH_IN###

def cash_in(account_id, amount):
    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValueError("Cash-in amount must be greater than zero")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT balance, account_status
                FROM accounts
                WHERE account_id = %s
                FOR UPDATE;
                """,
                (account_id,),
            )

            account = cursor.fetchone()

            if account is None:
                raise ValueError("Account does not exist")

            old_balance = account[0]
            account_status = account[1]

            if account_status != "active":
                raise ValueError("Account is not active")

            new_balance = old_balance + amount

            cursor.execute(
                """
                UPDATE accounts
                SET balance = %s
                WHERE account_id = %s;
                """,
                (
                    new_balance,
                    account_id,
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
                    origin_account_id,
                    transaction_status
                )
                VALUES (
                    'application',
                    'CASH_IN',
                    %s,
                    %s,
                    %s,
                    %s,
                    'EXTERNAL_CASH',
                    0.00,
                    0.00,
                    FALSE,
                    %s,
                    'completed'
                )
                RETURNING transaction_id;
                """,
                (
                    amount,
                    f"A{account_id}",
                    old_balance,
                    new_balance,
                    account_id,
                ),
            )

            transaction_id = cursor.fetchone()[0]

    return transaction_id


####CASH_OUT###

def cash_out(account_id, amount):
    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValueError(
            "Cash-out amount must be greater than zero"
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT balance, account_status
                FROM accounts
                WHERE account_id = %s
                FOR UPDATE;
                """,
                (account_id,),
            )

            account = cursor.fetchone()

            if account is None:
                raise ValueError(
                    "Account does not exist"
                )

            old_balance = account[0]
            account_status = account[1]

            if account_status != "active":
                raise ValueError(
                    "Account is not active"
                )

            if old_balance < amount:
                raise ValueError(
                    "Insufficient funds"
                )

            proposed_new_balance = (
                old_balance - amount
            )

            prediction = predict_fraud(
                transaction_type="CASH_OUT",
                amount=amount,
                old_balance_origin=old_balance,
                new_balance_origin=(
                    proposed_new_balance
                ),
                old_balance_destination=0.00,
                new_balance_destination=0.00,
            )

            if prediction["predicted_fraud"]:
                transaction_status = "flagged"

            else:
                transaction_status = "completed"

                cursor.execute(
                    """
                    UPDATE accounts
                    SET balance = %s
                    WHERE account_id = %s;
                    """,
                    (
                        proposed_new_balance,
                        account_id,
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
                    origin_account_id,
                    transaction_status
                )
                VALUES (
                    'application',
                    'CASH_OUT',
                    %s,
                    %s,
                    %s,
                    %s,
                    'EXTERNAL_CASH',
                    0.00,
                    0.00,
                    FALSE,
                    %s,
                    %s
                )
                RETURNING transaction_id;
                """,
                (
                    amount,
                    f"A{account_id}",
                    old_balance,
                    proposed_new_balance,
                    account_id,
                    transaction_status,
                ),
            )

            transaction_id = cursor.fetchone()[0]

            store_fraud_prediction(
                cursor=cursor,
                transaction_id=transaction_id,
                prediction=prediction,
            )

    return transaction_id

def make_payment(account_id, merchant_id, amount):
    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero"
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    balance,
                    account_status,
                    account_type
                FROM accounts
                WHERE account_id = %s
                FOR UPDATE;
                """,
                (account_id,),
            )

            account = cursor.fetchone()

            if account is None:
                raise ValueError(
                    "Account does not exist"
                )

            old_balance = account[0]
            account_status = account[1]
            account_type = account[2]

            if account_status != "active":
                raise ValueError(
                    "Account is not active"
                )

            if account_type == "savings":
                raise ValueError(
                    "Savings accounts cannot make merchant payments"
                )

            if old_balance < amount:
                raise ValueError(
                    "Insufficient funds"
                )

            cursor.execute(
                """
                SELECT merchant_code
                FROM merchants
                WHERE merchant_id = %s;
                """,
                (merchant_id,),
            )

            merchant = cursor.fetchone()

            if merchant is None:
                raise ValueError(
                    "Merchant does not exist"
                )

            merchant_code = merchant[0]

            proposed_new_balance = (
                old_balance - amount
            )

            prediction = predict_fraud(
                transaction_type="PAYMENT",
                amount=amount,
                old_balance_origin=old_balance,
                new_balance_origin=(
                    proposed_new_balance
                ),
                old_balance_destination=0.00,
                new_balance_destination=0.00,
            )

            if prediction["predicted_fraud"]:
                transaction_status = "flagged"

            else:
                transaction_status = "completed"

                cursor.execute(
                    """
                    UPDATE accounts
                    SET balance = %s
                    WHERE account_id = %s;
                    """,
                    (
                        proposed_new_balance,
                        account_id,
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
                    origin_account_id,
                    merchant_id,
                    transaction_status
                )
                VALUES (
                    'application',
                    'PAYMENT',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    0.00,
                    0.00,
                    FALSE,
                    %s,
                    %s,
                    %s
                )
                RETURNING transaction_id;
                """,
                (
                    amount,
                    f"A{account_id}",
                    old_balance,
                    proposed_new_balance,
                    merchant_code,
                    account_id,
                    merchant_id,
                    transaction_status,
                ),
            )

            transaction_id = cursor.fetchone()[0]

            store_fraud_prediction(
                cursor=cursor,
                transaction_id=transaction_id,
                prediction=prediction,
            )

    return transaction_id

def debit_account(
    account_id,
    amount,
    destination_code="EXTERNAL_DEBIT",
):
    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValueError(
            "Debit amount must be greater than zero"
        )

    if not destination_code:
        raise ValueError(
            "Destination code is required"
        )

    if len(destination_code) > 20:
        raise ValueError(
            "Destination code cannot exceed 20 characters"
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT balance, account_status
                FROM accounts
                WHERE account_id = %s
                FOR UPDATE;
                """,
                (account_id,),
            )

            account = cursor.fetchone()

            if account is None:
                raise ValueError(
                    "Account does not exist"
                )

            old_balance = account[0]
            account_status = account[1]

            if account_status != "active":
                raise ValueError(
                    "Account is not active"
                )

            if old_balance < amount:
                raise ValueError(
                    "Insufficient funds"
                )

            proposed_new_balance = (
                old_balance - amount
            )

            prediction = predict_fraud(
                transaction_type="DEBIT",
                amount=amount,
                old_balance_origin=old_balance,
                new_balance_origin=(
                    proposed_new_balance
                ),
                old_balance_destination=0.00,
                new_balance_destination=0.00,
            )

            if prediction["predicted_fraud"]:
                transaction_status = "flagged"

            else:
                transaction_status = "completed"

                cursor.execute(
                    """
                    UPDATE accounts
                    SET balance = %s
                    WHERE account_id = %s;
                    """,
                    (
                        proposed_new_balance,
                        account_id,
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
                    origin_account_id,
                    transaction_status
                )
                VALUES (
                    'application',
                    'DEBIT',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    0.00,
                    0.00,
                    FALSE,
                    %s,
                    %s
                )
                RETURNING transaction_id;
                """,
                (
                    amount,
                    f"A{account_id}",
                    old_balance,
                    proposed_new_balance,
                    destination_code,
                    account_id,
                    transaction_status,
                ),
            )

            transaction_id = cursor.fetchone()[0]

            store_fraud_prediction(
                cursor=cursor,
                transaction_id=transaction_id,
                prediction=prediction,
            )

    return transaction_id