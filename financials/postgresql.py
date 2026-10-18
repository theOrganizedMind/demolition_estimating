import os
from dotenv import load_dotenv

try:
    import psycopg2
except ModuleNotFoundError:
    class _Psycopg2Fallback:
        class Error(Exception):
            """Fallback psycopg2.Error type when psycopg2 is unavailable."""

        @staticmethod
        def connect(**kwargs):
            raise RuntimeError(
                "psycopg2 is not installed. Install database dependencies or use local sample data fallback."
            )

    psycopg2 = _Psycopg2Fallback()

load_dotenv()  # Load environment variables from .env file.

HOST = os.getenv("POSTGRESQL_HOST")
PORT = os.getenv("POSTGRESQL_PORT")
DATABASE = os.getenv("DATABASE")
USER = os.getenv("POSTGRESQL_USER")
PASSWORD = os.getenv("POSTGRESQL_PASSWORD")


def get_db_connection():
    """Create and return a PostgreSQL connection using environment settings."""
    try:
        return psycopg2.connect(
            host=HOST,
            port=PORT,
            database=DATABASE,
            user=USER,
            password=PASSWORD,
        )
    except psycopg2.Error as exc:
        raise RuntimeError(
            "Unable to establish PostgreSQL connection using configured environment settings."
        ) from exc
