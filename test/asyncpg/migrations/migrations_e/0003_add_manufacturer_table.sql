CREATE TABLE manufacturer (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL
);
