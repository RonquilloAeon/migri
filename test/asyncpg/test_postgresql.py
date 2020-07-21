import pytest

from migri.backends.postgresql import PostgreSQLConnection
from test import QUERIES


@pytest.mark.parametrize(
    "query_element,expected_query,expected_values",
    [
        (QUERIES[0], "INSERT INTO mytable (a) VALUES ($1), ($2)", [150, 300]),
        (QUERIES[1], "UPDATE tbl SET info=$2 WHERE id=$1", [39, "ok"]),
        (QUERIES[2], "SELECT * FROM school", []),
        (
            QUERIES[3],
            "SELECT * FROM val WHERE (value < $1 AND status = $3) "
            "OR (value > $2 AND status = $3)",
            [20, 100, "ok"],
        ),
    ],
)
def test_compile(query_element, expected_query, expected_values):
    backend = PostgreSQLConnection("postgres")
    assert backend._compile(query_element) == {
        "query": expected_query,
        "values": expected_values,
    }
