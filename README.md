# migri
A super simple PostgreSQL migration tool that uses asyncpg.

## Getting started
### Install `migri`
Run `pip install https://github.com/RonquilloAeon/migri/archive/master.zip`

### Initialize
Run `migri init` to create the table that tracks migrations. Both `init` and `migrate` 
require database credentials which can be provided via arguments or environment variables:
- `--db-user` or `DB_USER`
- `--db-pass` or `DB_PASS`
- `--db-name` or `DB_NAME`
- `--db-host` or `DB_HOST` (default `localhost`)
- `--db-port` or `DB_PORT` (default `5432`)

### Create migrations
Create a `migrations` directory and add your migrations. Migrations are applied in 
lexicographical order (e.g. `0001_initial.sql` then `0002_add_user_data.py` and so on).

Currently `.sql` and `.py` files are supported. If you write a Python migration file, 
ensure that it contains an async function `migrate`. An instance of asyncpg's `Connection`
class will be passed into the function.

```python
async def migrate(conn) -> bool:
    await conn.execute('INSERT INTO categories (name) VALUES ($1)', 'Animals')
    return True
```

### Migrate
Run `migri migrate`.

### Migrate programmatically
Migri can be called with a shell script (e.g. when a container is starting) or you can
call migri yourself from your code:

```python
import asyncpg
from migri import run_initialization, run_migrations

async def migrate():
    conn = await asyncpg.connect(host="localhost", user="user", password="pass", database="sampledb")
    await run_migrations("migrations", conn)
```

## Testing
1. Run `docker-compose up` to start Postgresql
2. Install nox with `pip install nox`
3. Run `nox`

## Todos
- Don't record empty migrations - warn user
- Add dry run mode for testing migrations
- Output migration results
- Output success message for init
- Test modules not found
- Test/handle incorrect function signature
