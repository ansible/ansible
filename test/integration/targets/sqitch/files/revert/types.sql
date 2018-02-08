-- Revert ding:types from pg

BEGIN;

DROP TYPE IF EXISTS test1.test_type CASCADE;

COMMIT;
