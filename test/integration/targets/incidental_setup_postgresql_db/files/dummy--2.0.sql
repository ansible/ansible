CREATE OR REPLACE FUNCTION dummy_display_ext_version()
RETURNS text LANGUAGE SQL AS 'SELECT (''2.0'')::text';
