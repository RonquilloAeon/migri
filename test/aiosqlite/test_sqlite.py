import pytest

from migri.backends.sqlite import SQLiteConnection
from test import QUERIES


@pytest.mark.parametrize(
    "query_element,expected_query,expected_values",
    [
        (QUERIES[0], "INSERT INTO mytable (a) VALUES (?), (?)", [150, 300]),
        (QUERIES[1], "UPDATE tbl SET info=? WHERE id=?", ["ok", 39]),
        (QUERIES[2], "SELECT * FROM school", []),
        (
            QUERIES[3],
            "SELECT * FROM val WHERE (value < ? AND status = ?) "
            "OR (value > ? AND status = ?)",
            [20, "ok", 100, "ok"],
        ),
    ],
)
def test_compile(query_element, expected_query, expected_values):
    backend = SQLiteConnection("test.db")
    assert backend._compile(query_element) == {
        "query": expected_query,
        "values": expected_values,
    }
