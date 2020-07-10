CREATE TABLE quote_view (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    quote integer REFERENCES quote(id) NOT NULL,
    view_count integer NOT NULL
);
