from database.connection import get_connection


def create_customer(first_name, last_name):
    sql = """
        INSERT INTO customers (
            first_name,
            last_name
        )
        VALUES (%s, %s)
        RETURNING customer_id, first_name, last_name;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (first_name, last_name))
            return cursor.fetchone()


def create_account(
    customer_id,
    account_type,
    starting_balance=0.00,
):
    sql = """
        INSERT INTO accounts (
            customer_id,
            account_type,
            balance
        )
        VALUES (%s, %s, %s)
        RETURNING
            account_id,
            customer_id,
            account_type,
            balance,
            account_status;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    customer_id,
                    account_type,
                    starting_balance,
                ),
            )

            return cursor.fetchone()

def create_merchant(merchant_code):
    sql = """
        INSERT INTO merchants (merchant_code)
        VALUES (%s)
        ON CONFLICT (merchant_code)
        DO UPDATE SET merchant_code = EXCLUDED.merchant_code
        RETURNING merchant_id, merchant_code;
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (merchant_code,))
            return cursor.fetchone()