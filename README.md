# migri
A super simple PostgreSQL migration tool that uses asyncpg.

## Getting started
### Install `migri`
### Create migrations table
```sql
CREATE TABLE applied_migration (
    id serial PRIMARY KEY,
    date_applied timestamp with time zone NOT NULL,
    name text NOT NULL
);
```
