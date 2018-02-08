-- Deploy ding:types to pg
-- requires: schemas

BEGIN;

CREATE TYPE test1.test_type AS (t1 TEXT, t2 INT, t3 INT);

COMMIT;
