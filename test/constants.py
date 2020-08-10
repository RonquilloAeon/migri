# DB connection details
MYSQL = {
    "db_user": "root",
    "db_pass": "passpass",
    "db_name": "migritestdb",
    "db_host": "127.0.0.1",
    "db_port": 3306,
}

POSTGRESQL = {
    "db_user": "migrator",
    "db_pass": "passpass",
    "db_name": "migritestdb",
    "db_host": "localhost",
    "db_port": "5432",
}

SQLITE = {
    "db_name": "test.db",
}

# Test migrations base dir
MIGRATIONS_BASE = "test/migrations"
