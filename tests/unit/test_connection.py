import pytest

from sdu_qm_task.connect import PSQLConnection


@pytest.fixture
def psql_connection():
    return PSQLConnection(
        dbname="dbname",
        user="user",
        password="password",
        host="host",
        port="port"
    )


def test_get_connection_string(psql_connection):
    assert psql_connection.get_connection_string() == "postgresql://user:password@host:port/dbname"
