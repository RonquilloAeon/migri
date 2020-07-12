CREATE TABLE satellite (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    catalog_number text NOT NULL,
    classification text NOT NULL
);
