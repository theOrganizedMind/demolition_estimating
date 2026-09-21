from unittest.mock import Mock

from estimate_project import postgresql


def test_get_db_connection_uses_module_settings(monkeypatch):
    connect_mock = Mock(return_value="fake-connection")
    monkeypatch.setattr(postgresql.psycopg2, "connect", connect_mock)

    postgresql.HOST = "localhost"
    postgresql.PORT = "5432"
    postgresql.DATABASE = "demo_db"
    postgresql.USER = "demo_user"
    postgresql.PASSWORD = "secret"

    connection = postgresql.get_db_connection()

    assert connection == "fake-connection"
    connect_mock.assert_called_once_with(
        host="localhost",
        port="5432",
        database="demo_db",
        user="demo_user",
        password="secret",
    )
