CREATE TABLE IF NOT EXISTS applied_migration (
    id serial PRIMARY KEY,
    date_applied timestamp with time zone NOT NULL,
    name text NOT NULL
);