# migri
A super simple PostgreSQL migration tool that uses asyncpg. You can use the CLI yourself,
in a shell script, or from your Python application.

## Coming soon!
MySql (aiomysql) and SQLite (aiosqlite) support will be added in version 1.0.0
(no later than September 23, 2020).

## Motivation
Using async database libraries is useful when a service/application is already using an
async library. It's extra overhead to install a synchronous library just to run migrations.
Practically speaking, though, there isn't much benefit to running migrations asynchronously
since migrations must be applied synchronously. Besides, the number of migrations for a
service is generally small.

## Getting started
### Install `migri`
Run `pip install migri[postgresql]`

### Create migrations
Create a `migrations` directory and add your migrations. Migrations are applied in 
lexicographical order (e.g. `0001_initial.sql` then `0002_add_user_data.py` and so on).

Currently `.sql` and `.py` files are supported. If you write a Python migration file, 
ensure that it contains an async function `migrate`. An instance of asyncpg's `Connection`
class will be passed into the function.

```python
async def migrate(conn) -> bool:
    await conn.execute("INSERT INTO categories (name) VALUES ($1)", "Animals")
    return True
```

### Migrate
Run `migri migrate`. Provide database credentials via arguments or environment variables:
- `--db-name` or `DB_NAME` (required)
- `--db-user` or `DB_USER`
- `--db-pass` or `DB_PASS`
- `--db-host` or `DB_HOST`
- `--db-port` or `DB_PORT`

Other options:
- `-d, --dialect` or `DB_DIALECT` (`mysql`, `postgresql`, `sqlite`,
  note that currently only `postgresql` is supported. If not set,
  `migri` will attempt to infer the dialect (and library to use)
  using the database port.)
- `-l, --log-level` or `LOG_LEVEL` (default `error`)

When you run `migrate`, `migri` will create a table called `applied_migration` (if it
doesn't exist). This is how `migri` tracks which migrations have already been applied.

#### Dry run mode
If you want to test your migrations without applying them, you can use the dry run
flag: `--dry-run`.

### Migrate programmatically
Migri can be called with a shell script (e.g. when a container is starting) or you can
apply migrations from your application:

```python
from migri import apply_migrations, PostgreSQLConnection

async def migrate():
    conn = PostgreSQLConnection(
        "sampledb",
        db_user="user",
        db_pass="passpass",
        db_host="localhost",
        db_port=5432
    )
    async with conn:
        await apply_migrations("migrations", conn)
```

## Testing
1. Set up local Python versions (e.g. `pyenv local 3.7.7 3.8.3`)
2. Run `docker-compose up` to start Postgresql.
3. Install nox with `pip install nox`.
4. Run `nox`.

## Docs
Docstrings are formatted in the [Sphinx](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html)
format.

## Todos
- [ ] Ensure that `migrate` command is safe to run even when no action need to be taken
  (e.g. helpful for container startup scripts)
- [x] Don't record empty migrations - warn user
- [x] Add dry run mode for testing migrations
- [x] Output migration results
- [ ] Test modules not found
- [x] Test/handle incorrect migrate function signature (in migration Python files)
- [ ] Add colorful output 🍭 for enhanced readability
- [ ] Make error output more readable
