CREATE OR REPLACE FUNCTION dummy_display_ext_version()
RETURNS text LANGUAGE SQL AS 'SELECT (''1.0'')::text';
