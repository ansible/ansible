-- Deploy ding:tests to pg
-- requires: schemas

BEGIN;

CREATE TABLE test1.tests(
    id              INT PRIMARY KEY,
    short_name      TEXT,
    description     TEXT
);

INSERT INTO test1.tests (id, short_name, description) VALUES (1,'first test','This is a first test');
INSERT INTO test1.tests (id, short_name, description) VALUES (2,'second test','This is a second test');

COMMIT;
