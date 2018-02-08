-- Verify ding:types on pg

BEGIN;

SELECT 1/COUNT(*) FROM pg_type WHERE typname = 'test_type';

ROLLBACK;
