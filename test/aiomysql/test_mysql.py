import pytest

from migri.backends.mysql import MySQLConnection
from test import QUERIES


@pytest.mark.parametrize(
    "query_element,expected_query,expected_values",
    [
        (QUERIES[0], "INSERT INTO mytable (a) VALUES (%s), (%s)", [150, 300]),
        (QUERIES[1], "UPDATE tbl SET info=%s WHERE id=%s", ["ok", 39]),
        (QUERIES[2], "SELECT * FROM school", []),
        (
            QUERIES[3],
            "SELECT * FROM val WHERE (value < %s AND status = %s) "
            "OR (value > %s AND status = %s)",
            [20, "ok", 100, "ok"],
        ),
    ],
)
def test_compile(query_element, expected_query, expected_values):
    backend = MySQLConnection("postgres")
    assert backend._compile(query_element) == {
        "query": expected_query,
        "values": expected_values,
    }
