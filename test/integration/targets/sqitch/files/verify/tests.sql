-- Verify ding:tests on pg

BEGIN;

SELECT id, short_name, description FROM test1.tests WHERE FALSE;

ROLLBACK;
