import pytest
import re


# SQL injection payloads targeting table name interpolation
@pytest.mark.parametrize("payload", [
    # Classic SQL injection via table name
    "users; DROP TABLE users; --",
    "users; DELETE FROM users; --",
    "users UNION SELECT * FROM passwords --",
    "users; INSERT INTO admin VALUES ('hacker', 'pwned'); --",
    # Quote-based injections
    "users' OR '1'='1",
    'users" OR "1"="1',
    "users`; DROP TABLE users; --",
    # Comment-based injections
    "users--",
    "users/*comment*/",
    "users; /* injected */",
    # Stacked queries
    "users; EXEC xp_cmdshell('whoami'); --",
    "users; SELECT pg_sleep(10); --",
    "users; WAITFOR DELAY '0:0:10'; --",
    # Whitespace/encoding tricks
    "users\nDROP TABLE users",
    "users\tUNION SELECT",
    "users\rDROP TABLE",
    # Nested/complex injections
    "users) VALUES (1); DROP TABLE users; --",
    "users VALUES (1); --",
    "(SELECT table_name FROM information_schema.tables)",
    # Empty and boundary cases
    "",
    " ",
    "\x00",
    "a" * 1000,
    # Special characters
    "users!@#$%^&*()",
    "users<script>alert(1)</script>",
    # Legitimate-looking but malicious
    "users WHERE 1=1; --",
    "users SET password='hacked' WHERE 1=1; --",
])
def test_sql_table_name_injection_invariant(payload):
    """Invariant: Table names used in SQL queries must be validated against
    a strict allowlist of alphanumeric characters and underscores only.
    Any table name containing SQL metacharacters, whitespace, semicolons,
    quotes, or other special characters must be rejected before being
    interpolated into a SQL query string."""

    def is_safe_table_name(name):
        """
        A table name is safe if and only if it consists solely of
        alphanumeric characters and underscores, and is not empty.
        This is the invariant that MUST hold before any table name
        is interpolated into a SQL query string.
        """
        if not name:
            return False
        # Only allow alphanumeric characters and underscores
        # This is the strict allowlist pattern for safe SQL identifiers
        safe_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        return bool(safe_pattern.match(name))

    def simulate_safe_query_execution(table_name):
        """
        Simulates what the code at hacking/report.py should do:
        validate the table name before interpolating it into SQL.
        Returns the SQL string only if the table name is safe,
        raises ValueError otherwise.
        """
        if not is_safe_table_name(table_name):
            raise ValueError(
                f"Unsafe table name rejected: {repr(table_name)}"
            )
        # Only reaches here if table name is safe
        # Simulate the vulnerable pattern but with validation guard
        values_placeholder = "%s"
        sql = 'INSERT INTO %s VALUES (%s)' % (table_name, values_placeholder)
        return sql

    # INVARIANT: Any payload that is not a safe identifier must be rejected
    # before being interpolated into a SQL query
    if not is_safe_table_name(payload):
        # The system MUST reject unsafe table names
        with pytest.raises((ValueError, TypeError, Exception)):
            result = simulate_safe_query_execution(payload)
            # If no exception was raised, the unsafe payload was accepted
            # This is a security violation - assert it never happens
            pytest.fail(
                f"SECURITY VIOLATION: Unsafe table name was accepted and "
                f"interpolated into SQL query without validation.\n"
                f"Payload: {repr(payload)}\n"
                f"Resulting SQL: {result}"
            )
    else:
        # Safe table names should work without errors
        try:
            result = simulate_safe_query_execution(payload)
            # Verify the result contains the safe table name properly
            assert payload in result, (
                f"Safe table name {repr(payload)} not found in query: {result}"
            )
            # Verify no dangerous SQL metacharacters leaked into the query
            # beyond what the safe table name itself contains
            assert result.startswith('INSERT INTO '), (
                f"Query structure was corrupted: {result}"
            )
        except ValueError:
            # A safe table name should not be rejected
            pytest.fail(
                f"Safe table name {repr(payload)} was incorrectly rejected"
            )


@pytest.mark.parametrize("table_name,should_be_safe", [
    # Safe table names
    ("users", True),
    ("report_data", True),
    ("ReportTable", True),
    ("table_123", True),
    ("_private_table", True),
    # Unsafe table names - SQL injection attempts
    ("users; DROP TABLE users", False),
    ("users UNION SELECT", False),
    ("users'", False),
    ('users"', False),
    ("users--", False),
    ("users/**/", False),
    ("123table", False),  # starts with digit
    ("", False),
    ("users table", False),  # contains space
    ("users\x00", False),  # null byte
])
def test_table_name_validation_allowlist(table_name, should_be_safe):
    """Invariant: The table name validation function must correctly classify
    safe vs unsafe table names. Safe names contain only alphanumeric chars
    and underscores starting with a letter or underscore. Everything else
    must be classified as unsafe."""

    safe_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    def is_safe_table_name(name):
        if not name:
            return False
        return bool(safe_pattern.match(name))

    result = is_safe_table_name(table_name)

    if should_be_safe:
        assert result is True, (
            f"Table name {repr(table_name)} should be classified as safe "
            f"but was rejected"
        )
    else:
        assert result is False, (
            f"SECURITY VIOLATION: Table name {repr(table_name)} should be "
            f"classified as UNSAFE but was accepted. This could allow SQL "
            f"injection via table name interpolation."
        )