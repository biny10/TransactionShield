from database.connection import get_connection


with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM transactions;")
        transaction_count = cursor.fetchone()[0]

print(f"Transactions in PostgreSQL: {transaction_count:,}")