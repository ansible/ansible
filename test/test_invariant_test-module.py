import pytest
import subprocess
import sys
import os


@pytest.mark.parametrize("payload", [
    # Exact exploit case: command injection via shell metacharacters
    "test_module; rm -rf /tmp/test",
    # Alternative injection: subshell execution
    "$(whoami)",
    # Backtick injection
    "`id`",
    # Boundary case: valid input without metacharacters
    "valid_module_name",
    # Edge case: empty string
    "",
])
def test_shell_command_injection_safety(payload):
    """Invariant: Shell commands never include unsanitized user input"""
    # Import the actual production module
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hacking.test_module import main
    
    # Capture the actual command that would be executed
    executed_commands = []
    original_popen = subprocess.Popen
    
    def mock_popen(cmd, **kwargs):
        executed_commands.append(cmd)
        # Return a safe mock process that does nothing
        class MockProcess:
            def communicate(self):
                return (b"", b"")
        return MockProcess()
    
    # Temporarily replace subprocess.Popen to intercept commands
    subprocess.Popen = mock_popen
    
    try:
        # Call the actual production function with adversarial input
        # The vulnerable code expects module arguments; simulate that
        sys.argv = ["test_module.py", payload]
        main()
        
        # Security assertion: no shell metacharacters should reach Popen
        for cmd in executed_commands:
            # Check if dangerous shell metacharacters appear in the command
            dangerous_chars = [";", "$(", "`", "&&", "||", "|", ">", "<"]
            for char in dangerous_chars:
                assert char not in cmd, (
                    f"Shell metacharacter '{char}' found in command: {cmd}. "
                    f"User input '{payload}' was not properly sanitized."
                )
                
    finally:
        # Restore original Popen
        subprocess.Popen = original_popen