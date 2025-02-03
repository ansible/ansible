"""Unit tests for fault handler utilities."""

import os
import pytest
import tempfile
from ansible.module_utils.faulthandler import setup_process_fault_handler


def test_fault_handler_setup():
    """Test basic fault handler setup."""
    result = setup_process_fault_handler('test')
    assert result is True
    
    pid = os.getpid()
    expected_file = f"/tmp/ansible-test-{pid}.stack"
    assert os.path.exists(expected_file)
    
    # Cleanup
    try:
        os.unlink(expected_file)
    except OSError:
        pass


def test_fault_handler_invalid_setup():
    """Test fault handler setup with invalid path."""
    
    # Create a temporary directory and make it read-only
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chmod(temp_dir, 0o444) # Set directory to read-only

        # Attempt to create a fault handler file in the read-only directory
        result = setup_process_fault_handler(f"{temp_dir}/test")

        # Ensure that the setup fails due to permission issues
        assert result is False
