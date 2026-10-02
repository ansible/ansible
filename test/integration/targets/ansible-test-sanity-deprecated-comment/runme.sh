#!/usr/bin/env bash

set -eu

SCRIPT_PATH="$ANSIBLE_TEST_ANSIBLE_LIB_ROOT/../../test/sanity/code-smell/deprecated-comment.py"
RESULTS="$OUTPUT_DIR/deprecated_comments_results.txt"

export ANSIBLE_TEST_CONTROLLER_PYTHON_VERSIONS="3.13,3.14"
export ANSIBLE_TEST_REMOTE_ONLY_PYTHON_VERSIONS="3.9,3.10"

python "$SCRIPT_PATH" \
    test_cases.py test_cases.sh test_cases.cs test_cases.ps1 \
    test_cases.yml test_cases.yaml \
    -- test_cases_target.py | tee "$RESULTS"

# Lines 1-3 are valid deprecations with future versions — no errors expected
if grep -q "test_cases.py:1:" "$RESULTS"; then
    echo "FAIL: line 1 should not produce an error" >&2
    exit 1
fi
if grep -q "test_cases.py:2:" "$RESULTS"; then
    echo "FAIL: line 2 should not produce an error" >&2
    exit 1
fi
if grep -q "test_cases.py:3:" "$RESULTS"; then
    echo "FAIL: line 3 should not produce an error" >&2
    exit 1
fi

# Line 4: missing version
grep -q "test_cases.py:4:0: ansible-deprecated-version-comment-missing-version:" "$RESULTS"

# Line 5: invalid key (foo)
grep -q "test_cases.py:5:0: ansible-deprecated-version-comment-invalid-key:" "$RESULTS"

# Line 6: invalid keys (foo, baz)
grep -q "test_cases.py:6:0: ansible-deprecated-version-comment-invalid-key:" "$RESULTS"

# Line 7: empty deprecation comment
grep -q "test_cases.py:7:0: ansible-deprecated-version-comment-missing-version:" "$RESULTS"

# Line 8: empty description value is accepted (falls back to default), no error
if grep -q "test_cases.py:8:" "$RESULTS"; then
    echo "FAIL: line 8 should not produce an error (empty description= is valid)" >&2
    exit 1
fi

# Line 9: unknown key (foo,)
grep -q "test_cases.py:9:0: ansible-deprecated-version-comment-invalid-key:" "$RESULTS"

# Line 10: expired core version (inline comment after code)
grep -q "test_cases.py:10:11: ansible-deprecated-version-comment:" "$RESULTS"

# Line 11: expired python version (inline comment after code)
grep -q "test_cases.py:11:11: ansible-deprecated-python-version-comment:" "$RESULTS"

# Line 12: invalid version string
grep -q "test_cases.py:12:0: ansible-deprecated-version-comment-invalid-version:" "$RESULTS"

# Line 13: malformed shlex (unterminated quote)
grep -q "test_cases.py:13:0: ansible-deprecated-version-comment-invalid-syntax:" "$RESULTS"

# Line 14: both core and python versions expired — two errors
test "$(grep -c "test_cases.py:14:0:" "$RESULTS")" -eq 2

# Shell file: comment on line 3 (after shebang + blank line)
grep -q "test_cases.sh:3:0: ansible-deprecated-version-comment:" "$RESULTS"

# Target file: python_version='3.12' is NOT expired for target (min 3.9), no error
if grep -q "test_cases_target.py:1:" "$RESULTS"; then
    echo "FAIL: target line 1 should not produce an error (3.12 not expired for target python 3.9)" >&2
    exit 1
fi

# Target file: python_version='3.8' IS expired for target (min 3.9)
grep -q "test_cases_target.py:2:0: ansible-deprecated-python-version-comment:" "$RESULTS"

# .cs file: // comment prefix
grep -q "test_cases.cs:1:0: ansible-deprecated-version-comment:" "$RESULTS"

# .ps1 file
grep -q "test_cases.ps1:1:0: ansible-deprecated-version-comment:" "$RESULTS"

# .yml file: comment at root level
grep -q "test_cases.yml:1:0: ansible-deprecated-version-comment:" "$RESULTS"

# .yml file: comment after key:
grep -q "test_cases.yml:2:5: ansible-deprecated-version-comment:" "$RESULTS"

# .yml file: comment after key: value
grep -q "test_cases.yml:3:11: ansible-deprecated-version-comment:" "$RESULTS"

# .yaml file
grep -q "test_cases.yaml:1:0: ansible-deprecated-version-comment:" "$RESULTS"

echo "All checks passed."
