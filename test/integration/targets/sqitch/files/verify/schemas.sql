-- Verify ding:schemas on pg

BEGIN;

SELECT pg_catalog.has_schema_privilege('test1','usage');

ROLLBACK;
