-- Runs automatically the FIRST time the database container starts with an empty volume
-- (every *.sql file in /docker-entrypoint-initdb.d/ is executed once).
-- If the volume already contains a database, this file is ignored.
CREATE TABLE IF NOT EXISTS messages (
    id         SERIAL PRIMARY KEY,
    text       VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

INSERT INTO messages (text) VALUES ('Hello! This first message was created by database/init.sql.');
