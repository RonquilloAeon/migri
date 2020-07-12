CREATE TABLE school (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    city text NOT NULL,
    state text NOT NULL
);
