import pandas as pd

from database.connection import get_connection


SELECT_COLUMNS = """
    SELECT
        transaction_id,
        transaction_type,
        amount::DOUBLE PRECISION AS amount,
        old_balance_origin::DOUBLE PRECISION
            AS old_balance_origin,
        new_balance_origin::DOUBLE PRECISION
            AS new_balance_origin,
        old_balance_destination::DOUBLE PRECISION
            AS old_balance_destination,
        new_balance_destination::DOUBLE PRECISION
            AS new_balance_destination,
        is_fraud::INTEGER AS is_fraud
    FROM ml_training_features
"""


def query_to_dataframe(query, chunk_size=100_000):
    frames = []

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

            column_names = [
                description.name
                for description in cursor.description
            ]

            while True:
                rows = cursor.fetchmany(chunk_size)

                if not rows:
                    break

                frame = pd.DataFrame.from_records(
                    rows,
                    columns=column_names,
                )

                frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def load_training_data():
    query = SELECT_COLUMNS + """
        WHERE MOD(transaction_id, 10) BETWEEN 2 AND 9
          AND (
              is_fraud = TRUE
              OR MOD(transaction_id / 10, 10) = 0
          );
    """

    return query_to_dataframe(query)


def load_validation_data():
    query = SELECT_COLUMNS + """
        WHERE MOD(transaction_id, 10) = 1;
    """

    return query_to_dataframe(query)


def load_test_data():
    query = SELECT_COLUMNS + """
        WHERE MOD(transaction_id, 10) = 0;
    """

    return query_to_dataframe(query)