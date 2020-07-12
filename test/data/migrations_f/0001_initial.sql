CREATE TABLE student (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name text NOT NULL,
    last_name text NOT NULL,
    grade smallint NOT NULL
);
