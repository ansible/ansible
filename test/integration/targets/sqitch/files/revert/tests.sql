-- Revert ding:tests from pg

BEGIN;

DROP TABLE test1.tests;

COMMIT;
