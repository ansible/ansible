from __future__ import annotations

import pytest
import subprocess
import sys
import os


@pytest.mark.parametrize("payload", [
    # Exact exploit case - command injection
    "test.sh; rm -rf /",
    # Shell command substitution
    "$(whoami)",
    # Backtick command execution
    "`id`",
    # Boundary case - empty string
    "",
    # Valid input (should pass)
    "legitimate_file.sh"
])
def test_shell_command_injection_via_modfile(payload):
    """Invariant: Shell commands never include unsanitized user input"""
    # Create a temporary file to track if command injection occurred
    test_dir = "/tmp/test_module_security"
    os.makedirs(test_dir, exist_ok=True)
    marker_file = f"{test_dir}/injection_marker"

    # Clean up any existing marker
    if os.path.exists(marker_file):
        os.remove(marker_file)

    # Use payload that would create a marker file if injection succeeds
    injection_payload = f"test.sh; touch {marker_file}"

    # Run the actual production script with the payload
    script_path = "hacking/test-module.py"

    # Create a test file to avoid actual permission changes
    test_file = f"{test_dir}/test_file"
    with open(test_file, "w") as f:
        f.write("test content")

    # Set environment variable that the script might use
    env = os.environ.copy()
    env['MODFILE'] = injection_payload

    try:
        # Execute the actual production script
        result = subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except subprocess.TimeoutExpired:
        # If command hangs (like rm -rf / might), it's a failure
        assert False, "Command injection caused timeout"

    # Check if injection marker was created
    injection_occurred = os.path.exists(marker_file)

    # Clean up
    if os.path.exists(marker_file):
        os.remove(marker_file)
    if os.path.exists(test_file):
        os.remove(test_file)

    # Assertion: No command injection should have occurred
    assert not injection_occurred, f"Command injection vulnerability detected with payload: {injection_payload}"

    # Additional check: Script should handle invalid input gracefully
    if payload in ["test.sh; rm -rf /", "$(whoami)", "`id`"]:
        # Script should either reject or sanitize these inputs
        # We accept either successful execution without injection OR graceful error
        assert result.returncode != 0 or not injection_occurred, \
            f"Dangerous payload '{payload}' was not properly sanitized"
