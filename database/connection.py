import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


REQUIRED_DATABASE_VARIABLES = (
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
)


def get_database_config():
    missing_variables = [
        variable
        for variable in REQUIRED_DATABASE_VARIABLES
        if not os.getenv(variable)
    ]

    if missing_variables:
        missing_names = ", ".join(missing_variables)

        raise RuntimeError(
            f"Missing database configuration: {missing_names}"
        )

    try:
        database_port = int(os.environ["DB_PORT"])
    except ValueError as error:
        raise RuntimeError(
            "DB_PORT must be a valid integer"
        ) from error

    return {
        "host": os.environ["DB_HOST"],
        "port": database_port,
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


def get_connection():
    return psycopg.connect(
        **get_database_config(),
        connect_timeout=5,
    )