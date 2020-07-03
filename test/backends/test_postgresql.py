import pytest

from migri.backends.postgresql import PostgreSQLConnection
from migri.elements import Query

q1 = Query("INSERT INTO mytable (a) VALUES ($a), ($b)", values={"a": 150, "b": 300})

q2 = Query("UPDATE tbl SET info=$info WHERE id=$id", values={"id": 39, "info": "ok"})

q3 = Query("SELECT * FROM pg_type")

q4 = Query(
    "SELECT * FROM val WHERE (value < $value_a AND status = $status) "
    "OR (value > $value_b AND status = $status)",
    values={"value_a": 20, "value_b": 100, "status": "ok"},
)


@pytest.mark.parametrize(
    "query_element,expected_query,expected_value",
    [
        (q1, "INSERT INTO mytable (a) VALUES ($1), ($2)", [150, 300]),
        (q2, "UPDATE tbl SET info=$2 WHERE id=$1", [39, "ok"]),
        (q3, "SELECT * FROM pg_type", []),
        (
            q4,
            "SELECT * FROM val WHERE (value < $1 AND status = $3) "
            "OR (value > $2 AND status = $3)",
            [20, 100, "ok"],
        ),
    ],
)
def test_compile(query_element, expected_query, expected_value):
    backend = PostgreSQLConnection("postgres")
    assert backend._compile(query_element) == {
        "query": expected_query,
        "values": expected_value,
    }
