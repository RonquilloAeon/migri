CREATE TABLE account (
    id serial PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE app_user (
    id serial PRIMARY KEY,
    account_id integer REFERENCES account,
    first_name text NOT NULL,
    last_name text NOT NULL,
    email text NOT NULL,
    password text NOT NULL
);