-- Revert ding:schemas from pg

BEGIN;

DROP SCHEMA IF EXISTS test1 CASCADE;

COMMIT;
