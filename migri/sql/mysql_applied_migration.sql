CREATE TABLE IF NOT EXISTS applied_migration (
    id integer NOT NULL AUTO_INCREMENT,
    date_applied datetime NOT NULL,
    name text NOT NULL,
    PRIMARY KEY (id)
);
