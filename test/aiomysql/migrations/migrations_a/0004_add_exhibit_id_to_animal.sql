ALTER TABLE animal
ADD COLUMN exhibit_id integer,
ADD FOREIGN KEY (exhibit_id) REFERENCES exhibit(id) ON DELETE RESTRICT;
