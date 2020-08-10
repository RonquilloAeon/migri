from subprocess import Popen, PIPE


def _create_postgresql_args(connection_details: dict) -> list:
    return [
        "migri",
        "-n",
        connection_details["db_name"],
        "-u",
        connection_details["db_user"],
        "-s",
        connection_details["db_pass"],
        "-p",
        connection_details["db_port"],
        "migrate",
    ]


# def test_migrate_postgres(
#     migrations, postgresql_conn_factory, postgresql_connection_details, postgresql_db
# ):
#     p = Popen(_create_postgresql_args(postgresql_connection_details), stdout=PIPE)
#     stdout, _ = p.communicate()
