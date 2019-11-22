# migri
A super simple PostgreSQL migration tool that uses asyncpg.

## Getting started
### Install `migri`
Run `pip install https://github.com/RonquilloAeon/migri/archive/master.zip`

### Initialize
Run `migri init` to create the table that tracks migrations.

### Create migrations

### Migrate

## Testing
1. Run `docker-compose up` to start Postgresql
2. Install nox with `pip install nox`
3. Run `nox`

## Todos
- Don't record empty migrations - warn user
- Output migration results
- Output success message for init
- Test modules not found
- Test/handle incorrect function signature
- Add doc info to README
