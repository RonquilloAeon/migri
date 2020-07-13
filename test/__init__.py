from migri.elements import Query

q1 = Query("INSERT INTO mytable (a) VALUES ($a), ($b)", values={"a": 150, "b": 300})
q2 = Query("UPDATE tbl SET info=$info WHERE id=$id", values={"id": 39, "info": "ok"})
q3 = Query("SELECT * FROM school")
q4 = Query(
    "SELECT * FROM val WHERE (value < $value_a AND status = $status) "
    "OR (value > $value_b AND status = $status)",
    values={"value_a": 20, "value_b": 100, "status": "ok"},
)

QUERIES = [q1, q2, q3, q4]
