CREATE TABLE state_machine (
    id serial PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE state_history (
    id serial PRIMARY KEY,
    machine_id integer REFERENCES state_machine,
    recorded_at timestamp NOT NULL DEFAULT(current_timestamp),
    trigger_name text NOT NULL,
    from_state text NOT NULL,
    to_state text NOT NULL
);
