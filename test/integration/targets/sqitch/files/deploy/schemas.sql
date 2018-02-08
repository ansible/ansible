-- Deploy ding:schemas to pg

BEGIN;

CREATE SCHEMA test1;
REVOKE ALL ON SCHEMA test1 FROM public;

COMMIT;
