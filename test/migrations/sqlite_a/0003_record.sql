CREATE TABLE record (
    id serial PRIMARY KEY,
    account integer REFERENCES account(id) NOT NULL,
    content text NOT NULL
);
